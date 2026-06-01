#!/usr/bin/env python3
"""Browser-driven full pipeline check for the 2FA doorlock app."""

from __future__ import annotations

import json
import os
import pty
import select
import socket
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = REPO_ROOT / "server"

os.environ["DOORLOCK_VISION_MOCK"] = "true"
os.environ["DOORLOCK_YOLO_ENABLED"] = "false"
os.environ["DOORLOCK_FACE_LIVENESS_REQUIRED"] = "false"
os.environ["DOORLOCK_ALLOW_UNENROLLED_FACE"] = "false"
os.environ["DOORLOCK_MOCK_FACE_IDENTITY"] = "gui-enrolled-person"
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "4")

if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))


class CheckFailure(RuntimeError):
    pass


def ok(message: str) -> None:
    print(f"[OK] {message}")


def fail(message: str) -> None:
    raise CheckFailure(message)


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_for_web(base: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(base + "/", timeout=0.5) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.05)
    fail("Web server did not become ready.")


def read_pty_until(fd: int, expected: str, timeout: float = 3.0) -> list[str]:
    deadline = time.monotonic() + timeout
    buffer = b""
    lines: list[str] = []
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], max(0.0, deadline - time.monotonic()))
        if not ready:
            continue
        chunk = os.read(fd, 1024)
        if not chunk:
            continue
        buffer += chunk
        while b"\n" in buffer:
            raw, buffer = buffer.split(b"\n", 1)
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            lines.append(line)
            if line == expected:
                return lines
    fail(f"Expected serial command {expected!r}, got {lines!r}")


def run_browser_flow(base: str, master_fd: int, server, vision) -> None:
    try:
        from playwright.sync_api import expect, sync_playwright
    except ModuleNotFoundError:
        fail("Playwright is not installed. Run this check with .venv/bin/python after installing project requirements.")

    chrome_path = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")
    if not Path(chrome_path).exists():
        fail(f"Chrome executable not found: {chrome_path}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=chrome_path,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(viewport={"width": 1280, "height": 920})
        context.add_init_script(
            """
            window.confirm = () => true;
            window.bootstrap = window.bootstrap || {
              Modal: class { constructor() {} show() {} hide() {} }
            };
            """
        )
        page = context.new_page()
        try:
            page.goto(base + "/register", wait_until="domcontentloaded")
            expect(page.locator("#btnCapture")).to_be_visible(timeout=5000)
            page.locator("#btnCapture").click()
            expect(page.locator("#captureMsg")).to_contain_text("Mock face captured", timeout=5000)

            page.locator("#name").fill("Gui Mock User")
            page.locator("#nfc_uid").fill("A1B2C3D4")
            page.locator("#password").fill("1234")
            page.locator("#btnSubmit").click()
            expect(page.locator("#msg")).to_contain_text("registered successfully", timeout=5000)
            ok("GUI registration captured mock face and created user")

            page.goto(base + "/users_page", wait_until="domcontentloaded")
            expect(page.locator("#user-body")).to_contain_text("Gui Mock User", timeout=5000)
            expect(page.locator("#user-body")).to_contain_text("A1B2C3D4", timeout=5000)
            ok("GUI users page shows registered identity")

            vision.set_mock_face_identity("gui-impostor")
            os.write(master_fd, b"WAKEUP:NFC:A1B2C3D4\n")
            read_pty_until(master_fd, "AUTH_FAIL")
            ok("registered NFC with wrong mock face is rejected")

            vision.set_mock_face_identity("gui-enrolled-person")
            server.last_failed_attempt = 0
            os.write(master_fd, b"WAKEUP:NFC:A1B2C3D4\n")
            read_pty_until(master_fd, "OPEN_DOOR")
            ok("registered NFC with matching mock face opens door")

            server.last_failed_attempt = 0
            os.write(master_fd, b"WAKEUP:PW:0000\n")
            read_pty_until(master_fd, "AUTH_FAIL")
            ok("bad PIN is rejected and sends AUTH_FAIL")

            page.goto(base + "/", wait_until="domcontentloaded")
            expect(page.locator("#status-arduino-line")).to_contain_text("연결됨", timeout=7000)
            expect(page.locator("#status-camera-line")).to_contain_text("모의 얼굴 인증 모드", timeout=7000)
            expect(page.get_by_role("button", name="Arduino 재연결")).to_be_visible(timeout=5000)
            expect(page.get_by_role("button", name="ESP32-CAM 재연결")).to_be_visible(timeout=5000)
            page.get_by_role("button", name="ESP32-CAM 재연결").click()
            expect(page.locator("#status-event-line")).to_contain_text("카메라", timeout=5000)
            ok("dashboard GUI shows hardware link status and retry controls")

            page.goto(base + "/hardware", wait_until="domcontentloaded")
            expect(page.locator("#hardware-title")).to_be_visible(timeout=5000)
            expect(page.locator("#status-arduino-line")).to_contain_text("연결됨", timeout=7000)
            expect(page.locator("#status-camera-line")).to_contain_text("모의 얼굴 인증 모드", timeout=7000)
            expect(page.get_by_role("button", name="Arduino 재연결")).to_be_visible(timeout=5000)
            expect(page.get_by_role("button", name="ESP32-CAM 재연결")).to_be_visible(timeout=5000)
            page.get_by_role("button", name="전체 재연결").click()
            expect(page.locator("#status-event-line")).to_contain_text("전체 재연결", timeout=5000)
            ok("hardware GUI shows device panels and reconnect controls")

            page.goto(base + "/", wait_until="domcontentloaded")
            page.wait_for_function(
                """
                () => {
                  const text = document.querySelector('#log-body')?.innerText || '';
                  return text.includes('FINAL_SUCCESS')
                    && text.includes('FINAL_FAIL')
                    && text.includes('UNAUTHORIZED');
                }
                """,
                timeout=7000,
            )
            ok("dashboard GUI renders success, face-fail, and unauthorized logs")

            page.get_by_role("button", name="문 열기").click()
            read_pty_until(master_fd, "OPEN_DOOR")
            page.get_by_role("button", name="긴급 잠금").click()
            read_pty_until(master_fd, "LOCKDOWN")
            ok("dashboard GUI manual controls send serial commands")

            page.goto(base + "/users_page", wait_until="domcontentloaded")
            expect(page.locator(".delete-btn").first).to_be_visible(timeout=5000)
            page.locator(".delete-btn").first.click()
            expect(page.locator("#user-body")).to_contain_text("등록된 사용자가 없습니다.", timeout=5000)
            users = page.evaluate("() => fetch('/api/users').then(r => r.json())")
            if users != []:
                fail(f"User deletion did not persist through API: {users!r}")
            ok("GUI delete removes identity")

            page.goto(base + "/", wait_until="domcontentloaded")
            page.wait_for_function(
                "() => (document.querySelector('#log-body')?.innerText || '').includes('알 수 없음')",
                timeout=7000,
            )
            capture_dir = REPO_ROOT / "captures"
            capture_dir.mkdir(exist_ok=True)
            page.screenshot(path=str(capture_dir / "gui_pipeline_dashboard.png"), full_page=True)
            ok("logs remain visible after user deletion with Unknown identity")
        finally:
            browser.close()


def main() -> int:
    import uvicorn
    import main as doorlock_main
    import web_app
    from database import Database
    from main import DoorLockServer
    from vision_ai import VisionAI

    master_fd, slave_fd = pty.openpty()
    slave_path = os.ttyname(slave_fd)
    old_serial_port = doorlock_main.SERIAL_PORT
    doorlock_main.SERIAL_PORT = slave_path

    running = True
    serial_errors: list[str] = []

    with tempfile.TemporaryDirectory(prefix="doorlock-gui-pipeline-") as tmp:
        db = Database(db_path=str(Path(tmp) / "doorlock.db"))
        vision = VisionAI(mock=True)
        server = DoorLockServer(db=db, vision=vision)
        server.rate_limit_seconds = 0
        server.lockdown_failure_limit = 10000
        server.lockdown_delay_seconds = 0
        web_app.configure_services(
            database=db,
            vision_ai=vision,
            command_callback=server.send_command,
            doorlock_server=server,
        )
        if hasattr(web_app.app.state, "last_capture"):
            del web_app.app.state.last_capture

        def serial_loop():
            while running:
                try:
                    server.process_serial_once()
                except Exception as exc:
                    serial_errors.append(str(exc))
                    break
                time.sleep(0.002)

        serial_thread = threading.Thread(target=serial_loop, daemon=True)
        serial_thread.start()

        port = free_port()
        uvicorn_server = uvicorn.Server(
            uvicorn.Config(web_app.app, host="127.0.0.1", port=port, log_level="critical")
        )
        web_thread = threading.Thread(target=uvicorn_server.run, daemon=True)
        web_thread.start()
        base = f"http://127.0.0.1:{port}"

        try:
            wait_for_web(base)
            run_browser_flow(base, master_fd, server, vision)

            if serial_errors:
                fail(f"Serial loop failed: {serial_errors}")

            logs = db.get_recent_logs(limit=20)
            statuses = [log["status"] for log in logs]
            required = {"FINAL_SUCCESS", "FINAL_FAIL", "UNAUTHORIZED"}
            if not required.issubset(statuses):
                fail(f"Missing expected log statuses. got={statuses}")

            print("GUI_FULL_PIPELINE_OK")
            return 0
        except CheckFailure as exc:
            print(f"\n[FAIL] {exc}")
            return 1
        finally:
            running = False
            serial_thread.join(timeout=2)
            uvicorn_server.should_exit = True
            web_thread.join(timeout=3)
            server.shutdown()
            web_app.configure_services(database=None, vision_ai=None, command_callback=None, doorlock_server=None)
            doorlock_main.SERIAL_PORT = old_serial_port
            os.close(master_fd)
            os.close(slave_fd)


if __name__ == "__main__":
    raise SystemExit(main())
