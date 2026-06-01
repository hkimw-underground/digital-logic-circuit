#!/usr/bin/env python3
"""Tomorrow demo/live validation for the 2FA doorlock project."""

from __future__ import annotations

import argparse
import glob
import json
import os
import pty
import select
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = REPO_ROOT / "server"
ARDUINO_CLI = REPO_ROOT / "bin" / "arduino-cli"
MAIN_SKETCH = REPO_ROOT / "arduino" / "doorlock_firmware" / "doorlock_firmware.ino"
TTP229_SKETCH = REPO_ROOT / "arduino" / "ttp229_test" / "ttp229_test.ino"
ESP32CAM_SKETCH = REPO_ROOT / "esp32cam" / "serial_camera" / "serial_camera.ino"


def load_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_dotenv()
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "4")

if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))


class CheckFailure(RuntimeError):
    pass


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str) -> None:
    raise CheckFailure(message)


def run_cmd(cmd: list[str], timeout: int | None = None) -> str:
    print("+ " + " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    print(result.stdout.rstrip())
    if result.returncode != 0:
        fail(f"Command failed with exit code {result.returncode}: {' '.join(cmd)}")
    return result.stdout


def check_python_stack() -> None:
    section("Python/vision stack")
    import cv2
    import dlib
    import face_recognition
    import torch
    import torchvision
    import ultralytics

    ok(f"cv2 {cv2.__version__}")
    ok(f"face_recognition {getattr(face_recognition, '__version__', 'unknown')}")
    ok(f"dlib {dlib.__version__}")
    ok(f"ultralytics {ultralytics.__version__}")
    ok(f"torch {torch.__version__}, cuda_available={torch.cuda.is_available()}")
    ok(f"torchvision {torchvision.__version__}")
    ok(f"torch threads={torch.get_num_threads()}")
    run_cmd([sys.executable, "-m", "pip", "check"], timeout=60)


def check_env() -> None:
    section("Runtime env")
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        fail(".env is missing. Run ./setup.sh or recreate it before tomorrow.")
    ok(".env exists")

    keys = [
        "DOORLOCK_SERIAL_PORT",
        "DOORLOCK_CAMERA_URL",
        "DOORLOCK_VISION_MOCK",
        "DOORLOCK_YOLO_ENABLED",
        "DOORLOCK_FACE_LIVENESS_REQUIRED",
        "OMP_NUM_THREADS",
    ]
    for key in keys:
        print(f"{key}={os.environ.get(key, '(unset)')}")

    yolo_enabled = os.environ.get("DOORLOCK_YOLO_ENABLED", "").lower() in {"1", "true", "yes", "on"}
    model_path = REPO_ROOT / "models" / "doorlock_yolov8n.pt"
    if yolo_enabled and not model_path.exists():
        fail("YOLO is enabled but models/doorlock_yolov8n.pt is missing.")
    if not yolo_enabled:
        ok("YOLO disabled for stable live face matching")


def compile_sketches() -> None:
    section("Arduino compile")
    if not ARDUINO_CLI.exists():
        fail(f"arduino-cli not found: {ARDUINO_CLI}")
    fqbn = "arduino:renesas_uno:unor4wifi"
    run_cmd([str(ARDUINO_CLI), "compile", "--fqbn", fqbn, str(MAIN_SKETCH)], timeout=120)
    run_cmd([str(ARDUINO_CLI), "compile", "--fqbn", fqbn, str(TTP229_SKETCH)], timeout=120)
    run_cmd([str(ARDUINO_CLI), "compile", "--fqbn", "esp32:esp32:esp32cam", str(ESP32CAM_SKETCH)], timeout=120)


def detect_serial_port() -> str:
    env_port = os.environ.get("DOORLOCK_SERIAL_PORT")
    if env_port and Path(env_port).exists():
        return env_port
    candidates = sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*"))
    if candidates:
        return candidates[0]
    return env_port or "/dev/ttyACM0"


def check_camera_and_face(timeout: float) -> None:
    section("Camera and face capture")
    import cv2
    import face_recognition
    from vision_ai import VisionAI

    if sys.stdin.isatty():
        input("Sit in front of the camera, make sure your face is visible, then press Enter.")
    else:
        print("Make sure a face is visible to the camera. Non-interactive run starts now.")

    camera_url = os.environ.get("DOORLOCK_CAMERA_URL", "0")
    vision = VisionAI(mock=False)
    if not vision.camera_available:
        fail(f"Camera did not open: {camera_url}")

    deadline = time.monotonic() + timeout
    frame_shape = None
    face_count = 0
    encoding_count = 0
    last_frame = None
    last_progress = 0.0
    try:
        while time.monotonic() < deadline:
            ret, frame = vision._read_camera_frame()
            if not ret:
                time.sleep(0.05)
                continue
            frame_shape = frame.shape
            last_frame = frame.copy()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb, model="hog")
            face_count = max(face_count, len(locations))
            if locations:
                encodings = face_recognition.face_encodings(rgb, locations)
                encoding_count = len(encodings)
                if encodings:
                    ok(f"camera={camera_url}, frame={frame_shape}, faces={len(locations)}, encodings={encoding_count}")
                    return
            now = time.monotonic()
            if now - last_progress > 3.0:
                print(f"waiting for face... frame={frame_shape}, max_faces={face_count}")
                last_progress = now
            time.sleep(0.05)
    finally:
        vision.release()

    if last_frame is not None:
        capture_dir = REPO_ROOT / "captures"
        capture_dir.mkdir(exist_ok=True)
        capture_path = capture_dir / "preflight_camera.jpg"
        cv2.imwrite(str(capture_path), last_frame)
        warn(f"Last camera frame saved: {capture_path}")

    fail(
        "Camera opened but no face encoding was captured. "
        f"frame={frame_shape}, max_faces={face_count}. Sit in front of the camera and rerun."
    )


def live_face_verify() -> None:
    section("Real face capture and verify")
    from database import Database
    from vision_ai import VisionAI

    with tempfile.TemporaryDirectory(prefix="doorlock-live-face-") as tmp:
        db = Database(db_path=str(Path(tmp) / "doorlock.db"))
        vision = VisionAI(mock=None)
        try:
            if not vision.camera_available:
                fail("VisionAI camera is not available.")
            encoding, message = vision.capture_face_encoding()
            if not encoding:
                fail(f"Face capture failed: {message}")
            user_id = db.add_user("TomorrowFace", nfc_uid="FACECAFE", password="1234", face_encoding=encoding)
            if not user_id:
                fail("Could not insert temporary face user.")
            if not vision.verify_face(user_id, db):
                fail("Face verification failed after successful capture.")
            ok("real camera capture + stored face verification passed")
        finally:
            vision.release()
            db.close()


class MockFaceVision:
    """Deterministic face-vector stand-in for full pipeline tests without a camera."""

    def __init__(self):
        import face_recognition
        import numpy as np
        from vision_ai import VisionAI

        self.camera = None
        self.camera_available = False
        self.face_recognition = face_recognition
        self.np = np
        self.codec = VisionAI(mock=True)
        self.encoding = np.linspace(-0.25, 0.25, self.codec.FACE_ENCODING_SIZE, dtype=np.float64)

    def capture_face_encoding(self):
        payload = self.codec._serialize_face_encoding(self.encoding)
        return payload, "Mock face captured successfully."

    def verify_face(self, user_id, db):
        stored_encoding_bytes = db.get_face_encoding(user_id)
        if not stored_encoding_bytes:
            print(f"[MOCK_FACE] No stored face encoding for user {user_id}")
            return False

        try:
            stored_encoding = self.codec._deserialize_face_encoding(stored_encoding_bytes)
        except Exception as exc:
            print(f"[MOCK_FACE] Stored face encoding is invalid: {exc}")
            return False

        matches = self.face_recognition.compare_faces([stored_encoding], self.encoding, tolerance=0.01)
        if True in matches:
            print(f"[MOCK_FACE] Face vector verified for user {user_id}")
            return True

        distance = self.np.linalg.norm(stored_encoding - self.encoding)
        print(f"[MOCK_FACE] Face vector mismatch for user {user_id}: distance={distance:.6f}")
        return False

    def release(self):
        self.codec.release()


def _http_post(base: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base + path, data=data, method="POST")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _http_get(base: str, path: str) -> tuple[int, dict | list]:
    with urllib.request.urlopen(base + path, timeout=15) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def web_serial_face_e2e() -> None:
    section("Web + serial + real face E2E")
    import uvicorn
    import main as doorlock_main
    import web_app
    from database import Database
    from main import DoorLockServer
    from vision_ai import VisionAI

    master_fd, slave_fd = pty.openpty()
    slave_path = os.ttyname(slave_fd)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    old_serial_port = doorlock_main.SERIAL_PORT
    doorlock_main.SERIAL_PORT = slave_path

    with tempfile.TemporaryDirectory(prefix="doorlock-live-e2e-") as tmp:
        db = Database(db_path=str(Path(tmp) / "doorlock.db"))
        vision = VisionAI(mock=None)
        server = DoorLockServer(db=db, vision=vision)
        server.rate_limit_seconds = 0
        server.lockdown_failure_limit = 10000
        web_app.configure_services(
            database=db,
            vision_ai=vision,
            command_callback=server.send_command,
            doorlock_server=server,
        )
        if hasattr(web_app.app.state, "last_capture"):
            del web_app.app.state.last_capture

        uvicorn_server = uvicorn.Server(
            uvicorn.Config(web_app.app, host="127.0.0.1", port=port, log_level="critical")
        )
        thread = threading.Thread(target=uvicorn_server.run, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                try:
                    with urllib.request.urlopen(base + "/", timeout=0.5) as response:
                        if response.status == 200:
                            break
                except Exception:
                    time.sleep(0.05)
            else:
                fail("Web server did not start.")

            status, capture = _http_post(base, "/api/capture_face")
            if status != 200 or not capture.get("success"):
                fail(f"Web face capture failed: {capture}")
            status, registered = _http_post(
                base,
                "/api/register",
                {"name": "LiveE2E", "nfc_uid": "ABCD1234", "password": "1234"},
            )
            if status != 200 or not registered.get("success"):
                fail(f"Web register failed: {registered}")

            os.write(master_fd, b"WAKEUP:NFC:ABCD1234\n")
            line = _wait_for_server_serial_process(server, timeout=5.0)
            if line != "WAKEUP:NFC:ABCD1234":
                fail(f"Server did not read expected WAKEUP line: {line!r}")

            command = _read_pty_line(master_fd, timeout=3.0)
            if command != "OPEN_DOOR":
                fail(f"Expected OPEN_DOOR from server, got {command!r}")
            ok("web capture/register + serial WAKEUP + real face verify + OPEN_DOOR passed")
        finally:
            uvicorn_server.should_exit = True
            thread.join(timeout=3)
            server.shutdown()
            doorlock_main.SERIAL_PORT = old_serial_port
            os.close(master_fd)
            os.close(slave_fd)


def mock_face_full_e2e() -> None:
    section("Web + serial + mock face full E2E")
    import uvicorn
    import main as doorlock_main
    import web_app
    from database import Database
    from main import DoorLockServer

    master_fd, slave_fd = pty.openpty()
    slave_path = os.ttyname(slave_fd)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    old_serial_port = doorlock_main.SERIAL_PORT
    doorlock_main.SERIAL_PORT = slave_path

    with tempfile.TemporaryDirectory(prefix="doorlock-mock-face-e2e-") as tmp:
        db = Database(db_path=str(Path(tmp) / "doorlock.db"))
        vision = MockFaceVision()
        server = DoorLockServer(db=db, vision=vision)
        server.rate_limit_seconds = 0
        server.lockdown_failure_limit = 10000
        web_app.configure_services(
            database=db,
            vision_ai=vision,
            command_callback=server.send_command,
            doorlock_server=server,
        )
        if hasattr(web_app.app.state, "last_capture"):
            del web_app.app.state.last_capture

        uvicorn_server = uvicorn.Server(
            uvicorn.Config(web_app.app, host="127.0.0.1", port=port, log_level="critical")
        )
        thread = threading.Thread(target=uvicorn_server.run, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                try:
                    with urllib.request.urlopen(base + "/", timeout=0.5) as response:
                        if response.status == 200:
                            break
                except Exception:
                    time.sleep(0.05)
            else:
                fail("Mock-face web server did not start.")

            status, capture = _http_post(base, "/api/capture_face")
            if status != 200 or not capture.get("success"):
                fail(f"Mock face capture failed: {capture}")
            status, registered = _http_post(
                base,
                "/api/register",
                {"name": "MockFaceUser", "nfc_uid": "ABCD1234", "password": "1234"},
            )
            if status != 200 or not registered.get("success"):
                fail(f"Mock face registration failed: {registered}")

            status, users = _http_get(base, "/api/users")
            matching_users = [user for user in users if user["username"] == "MockFaceUser"]
            if status != 200 or not matching_users:
                fail(f"Registered mock user not visible through /api/users: {users}")
            registered_user_id = matching_users[0]["id"]
            expected_encoding, _ = vision.capture_face_encoding()
            stored_encoding = db.get_face_encoding(registered_user_id)
            if stored_encoding != expected_encoding:
                fail("Registered mock user's face encoding was not persisted exactly in SQLite.")

            os.write(master_fd, b"WAKEUP:NFC:ABCD1234\n")
            line = _wait_for_server_serial_process(server, timeout=5.0)
            if line != "WAKEUP:NFC:ABCD1234":
                fail(f"Server did not read expected NFC WAKEUP line: {line!r}")

            command = _read_pty_line(master_fd, timeout=3.0)
            if command != "OPEN_DOOR":
                fail(f"Expected OPEN_DOOR from NFC+mock-face auth, got {command!r}")

            os.write(master_fd, b"WAKEUP:PW:0000\n")
            line = _wait_for_server_serial_process(server, timeout=5.0)
            if line != "WAKEUP:PW:0000":
                fail(f"Server did not read expected bad PIN WAKEUP line: {line!r}")

            command = _read_pty_line(master_fd, timeout=3.0)
            if command != "AUTH_FAIL":
                fail(f"Expected AUTH_FAIL from bad PIN, got {command!r}")

            status, lockdown = _http_post(base, "/api/control/lockdown")
            if status != 200 or not lockdown.get("success"):
                fail(f"Lockdown API failed: {lockdown}")
            command = _read_pty_line(master_fd, timeout=3.0)
            if command != "LOCKDOWN":
                fail(f"Expected LOCKDOWN command from web API, got {command!r}")

            status, logs = _http_get(base, "/api/logs")
            statuses = [entry["status"] for entry in logs.get("logs", [])]
            expected_statuses = ["UNAUTHORIZED", "FINAL_SUCCESS", "1ST_AUTH_SUCCESS"]
            if status != 200 or statuses[:3] != expected_statuses:
                fail(f"Expected FINAL_SUCCESS and UNAUTHORIZED logs, got {statuses}")

            ok("mock capture/register + serial NFC auth + OPEN_DOOR + bad PIN fail + lockdown API passed")
            print("MOCK_FACE_FULL_E2E_OK")
        finally:
            uvicorn_server.should_exit = True
            thread.join(timeout=3)
            server.shutdown()
            web_app.configure_services(database=None, vision_ai=None, command_callback=None, doorlock_server=None)
            doorlock_main.SERIAL_PORT = old_serial_port
            os.close(master_fd)
            os.close(slave_fd)


def _wait_for_server_serial_process(server, timeout: float) -> str | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = server.process_serial_once()
        if line:
            return line
        time.sleep(0.002)
    return None


def _read_pty_line(fd: int, timeout: float) -> str | None:
    deadline = time.monotonic() + timeout
    buffer = b""
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], max(0.0, deadline - time.monotonic()))
        if ready:
            buffer += os.read(fd, 1024)
            if b"\n" in buffer:
                return buffer.split(b"\n", 1)[0].decode(errors="ignore").strip()
    return None


def hardware_serial_check(actuate: bool, timeout: float) -> None:
    section("Physical Arduino serial")
    import serial

    port = detect_serial_port()
    if not Path(port).exists():
        fail(f"Serial port does not exist: {port}")
    ok(f"serial port candidate: {port}")

    with serial.Serial(port, 9600, timeout=0.2) as ser:
        print("Waiting for SYSTEM_READY or WAKEUP lines. Reset Arduino if needed.")
        deadline = time.monotonic() + timeout
        seen = []
        while time.monotonic() < deadline:
            raw = ser.readline()
            if raw:
                line = raw.decode(errors="ignore").strip()
                if line:
                    print(f"ARDUINO> {line}")
                    seen.append(line)
                    if line == "SYSTEM_READY":
                        break
        if not seen:
            fail("No serial data received from Arduino.")
        ok("Arduino serial is readable")

        input("Press Enter, then enter PIN on TTP229 or tap NFC. Waiting for WAKEUP...")
        deadline = time.monotonic() + timeout
        wakeup = None
        while time.monotonic() < deadline:
            raw = ser.readline()
            if raw:
                line = raw.decode(errors="ignore").strip()
                if line:
                    print(f"ARDUINO> {line}")
                    if line.startswith("WAKEUP:"):
                        wakeup = line
                        break
        if not wakeup:
            fail("No WAKEUP line received from keypad/NFC.")
        ok(f"input wakeup received: {wakeup}")

        if actuate:
            answer = input("Type OPEN to send OPEN_DOOR to the real servo: ").strip()
            if answer == "OPEN":
                ser.write(b"OPEN_DOOR\n")
                ok("OPEN_DOOR sent. Check servo movement and DOOR_OPENED/DOOR_CLOSED logs.")
            answer = input("Type FAIL to send AUTH_FAIL buzzer pattern: ").strip()
            if answer == "FAIL":
                ser.write(b"AUTH_FAIL\n")
                ok("AUTH_FAIL sent. Check buzzer.")
            answer = input("Type LOCKDOWN to send LOCKDOWN pattern: ").strip()
            if answer == "LOCKDOWN":
                ser.write(b"LOCKDOWN\n")
                ok("LOCKDOWN sent. Check buzzer/lockdown behavior.")
        else:
            warn("Actuator commands skipped. Rerun with --actuate to test servo/buzzer.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-compile", action="store_true", help="Skip Arduino compile checks.")
    parser.add_argument("--skip-face", action="store_true", help="Skip real camera face checks.")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip web+serial real-face software E2E.")
    parser.add_argument("--mock-face", action="store_true", help="Also run camera-free mock face full E2E.")
    parser.add_argument("--mock-face-only", action="store_true", help="Run env/package/compile and mock face E2E only.")
    parser.add_argument("--hardware", action="store_true", help="Also check real Arduino serial/keypad/NFC.")
    parser.add_argument("--actuate", action="store_true", help="Allow interactive OPEN_DOOR/AUTH_FAIL/LOCKDOWN commands.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Timeout for camera/serial waits.")
    args = parser.parse_args()

    try:
        check_env()
        check_python_stack()
        if not args.skip_compile:
            compile_sketches()
        if args.mock_face_only:
            mock_face_full_e2e()
            print("\nALL REQUESTED CHECKS PASSED")
            return 0
        if not args.skip_face:
            check_camera_and_face(timeout=args.timeout)
            live_face_verify()
        if not args.skip_e2e:
            web_serial_face_e2e()
        if args.mock_face:
            mock_face_full_e2e()
        if args.hardware:
            hardware_serial_check(actuate=args.actuate, timeout=args.timeout)
    except CheckFailure as exc:
        print(f"\n[FAIL] {exc}")
        return 1

    print("\nALL REQUESTED CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
