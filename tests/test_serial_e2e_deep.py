import os
import pty
import select
import sys
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("DOORLOCK_VISION_MOCK", "1")
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import serial  # noqa: F401
except Exception:
    serial = None

from database import Database
from main import DoorLockServer
from vision_ai import VisionAI


class _PTYSerialLink:
    def __init__(self):
        self.master_fd, self.slave_fd = pty.openpty()
        self.slave_path = os.ttyname(self.slave_fd)

    def send_line(self, line: str):
        if not line.endswith("\n"):
            line = f"{line}\n"
        os.write(self.master_fd, line.encode("utf-8"))

    def clear(self, timeout: float = 0.0):
        while True:
            ready, _, _ = select.select([self.master_fd], [], [], timeout)
            if not ready:
                break
            if not os.read(self.master_fd, 1024):
                break

    def read_lines(self, expected: int, timeout: float) -> list[str]:
        lines = []
        remainder = b""
        deadline = time.monotonic() + timeout
        while len(lines) < expected and time.monotonic() < deadline:
            remaining = max(0.0, deadline - time.monotonic())
            ready, _, _ = select.select([self.master_fd], [], [], remaining)
            if not ready:
                break
            data = os.read(self.master_fd, 1024)
            if not data:
                break
            remainder += data
            while b"\n" in remainder:
                raw_line, remainder = remainder.split(b"\n", 1)
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if line:
                    lines.append(line)
        return lines

    def close(self):
        os.close(self.master_fd)
        os.close(self.slave_fd)


@unittest.skipIf(serial is None, "pyserial is not installed")
class TestSerialE2EDeep(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "doorlock_test.db"
        self.db = Database(db_path=str(self.db_path))
        self.vision = VisionAI(mock=True)
        face_encoding, _ = self.vision.capture_face_encoding()
        self.db.add_user("Admin", nfc_uid="A1B2C3D4", password="1234", face_encoding=face_encoding)

        self.link = _PTYSerialLink()
        import main as doorlock_main
        self.main_module = doorlock_main
        self._orig_main_serial_port = doorlock_main.SERIAL_PORT
        doorlock_main.SERIAL_PORT = self.link.slave_path

        self.server = DoorLockServer(
            db=self.db,
            vision=self.vision,
        )
        self.server.rate_limit_seconds = 0
        self.server.lockdown_delay_seconds = 0

        if self.server.ser is None:
            self.fail("Failed to open PTY-backed serial connection.")

    def tearDown(self):
        self.main_module.SERIAL_PORT = self._orig_main_serial_port

        if getattr(self, "server", None) is not None:
            self.server.shutdown()
        if getattr(self, "link", None) is not None:
            self.link.close()
        if getattr(self, "db", None) is not None and self.db.conn is not None:
            self.db.close()
        self.temp_dir.cleanup()

    def _pump_one_input(self, timeout: float = 0.5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.server.ser.in_waiting <= 0:
                time.sleep(0.005)
                continue

            raw = self.server.ser.readline()
            if not raw:
                continue

            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            return line
        self.fail("No WAKEUP line arrived from PTY during timeout.")

    def _send_wakeup_and_handle(self, payload: str):
        self.link.send_line(payload)
        wakeup = self._pump_one_input()
        self.assertEqual(wakeup, payload)
        self.server.handle_wakeup(wakeup)

    def test_open_door_written_back_for_valid_wakeup(self):
        self.link.clear()
        self._send_wakeup_and_handle("WAKEUP:NFC:A1B2C3D4")
        commands = self.link.read_lines(1, timeout=1.0)

        self.assertIn("OPEN_DOOR", commands)

    def test_auth_fail_written_back_for_unknown_user(self):
        self.link.clear()
        self._send_wakeup_and_handle("WAKEUP:NFC:BADFACE01")
        commands = self.link.read_lines(1, timeout=1.0)

        self.assertIn("AUTH_FAIL", commands)

    def test_lockdown_written_back_after_failure_threshold(self):
        self.server.lockdown_failure_limit = 1
        self.server.last_failed_attempt = 0
        self.link.clear()

        self._send_wakeup_and_handle("WAKEUP:PW:0000")
        first = self.link.read_lines(1, timeout=1.0)
        self.assertIn("AUTH_FAIL", first)

        self._send_wakeup_and_handle("WAKEUP:PW:1111")
        second = self.link.read_lines(1, timeout=1.0)
        self.assertIn("LOCKDOWN", second)


if __name__ == "__main__":
    unittest.main()
