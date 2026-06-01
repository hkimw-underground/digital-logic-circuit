import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from database import Database
from main import DoorLockServer
from vision_ai import VisionAI


class ProbeSerial:
    opened_ports = []
    responses = {}

    def __init__(self, port, *args, **kwargs):
        self.port = port
        self.is_open = True
        self._buffer = bytearray()
        self.writes = []
        ProbeSerial.opened_ports.append(port)

    def write(self, data):
        self.writes.append(data)
        if data == b"PING\n":
            self._buffer.extend(self.responses.get(self.port, b""))
        return len(data)

    def flush(self):
        pass

    def readline(self):
        newline = self._buffer.find(b"\n")
        if newline < 0:
            return b""
        line = bytes(self._buffer[:newline + 1])
        del self._buffer[:newline + 1]
        return line

    @property
    def in_waiting(self):
        return len(self._buffer)

    def close(self):
        self.is_open = False


class TestSerialAutodetect(unittest.TestCase):
    def setUp(self):
        ProbeSerial.opened_ports = []
        ProbeSerial.responses = {
            "/dev/ttyACM0": b"PONG:DOORLOCK_ARDUINO\n",
            "/dev/ttyUSB0": b"PONG:READY\n",
        }
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(db_path=str(Path(self.temp_dir.name) / "doorlock.db"))

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_auto_scan_identifies_arduino_and_skips_esp32(self):
        import main as doorlock_main

        original_serial_port = doorlock_main.SERIAL_PORT
        doorlock_main.SERIAL_PORT = "auto"

        arduino = MagicMock(
            device="/dev/ttyACM0",
            description="Arduino UNO R4 WiFi",
            hwid="USB VID:PID=2341:1002",
            manufacturer="Arduino",
            product="UNO R4 WiFi",
        )
        esp32 = MagicMock(
            device="/dev/ttyUSB0",
            description="USB2.0-Serial CH340",
            hwid="USB VID:PID=1A86:7523",
            manufacturer="wch.cn",
            product="USB Serial",
        )
        xilinx = MagicMock(
            device="/dev/ttyUSB1",
            description="Xilinx USB JTAG",
            hwid="Xilinx",
            manufacturer="Xilinx",
            product="Digilent",
        )

        try:
            with patch("serial.tools.list_ports.comports", return_value=[esp32, xilinx, arduino]), \
                    patch.object(doorlock_main.glob, "glob", return_value=[]), \
                    patch.object(doorlock_main.serial, "Serial", ProbeSerial):
                server = DoorLockServer(db=self.db, vision=VisionAI(mock=True))
            try:
                self.assertEqual(server.serial_port, "/dev/ttyACM0")
                self.assertTrue(server.get_serial_status()["connected"])
                self.assertNotEqual(server.serial_port, "/dev/ttyUSB0")
            finally:
                server.shutdown()
        finally:
            doorlock_main.SERIAL_PORT = original_serial_port

    def test_auto_scan_does_not_accept_system_ready_without_pong(self):
        import main as doorlock_main

        original_serial_port = doorlock_main.SERIAL_PORT
        doorlock_main.SERIAL_PORT = "auto"
        ProbeSerial.responses = {"/dev/ttyACM0": b"SYSTEM_READY\n"}

        stale = MagicMock(
            device="/dev/ttyACM0",
            description="USB ACM device with stale boot line",
            hwid="USB VID:PID=9999:0001",
            manufacturer="",
            product="",
        )

        try:
            with patch("serial.tools.list_ports.comports", return_value=[stale]), \
                    patch.object(doorlock_main.glob, "glob", return_value=[]), \
                    patch.object(doorlock_main.serial, "Serial", ProbeSerial):
                server = DoorLockServer(db=self.db, vision=VisionAI(mock=True))
            try:
                self.assertIsNone(server.serial_port)
                self.assertFalse(server.get_serial_status()["connected"])
            finally:
                server.shutdown()
        finally:
            doorlock_main.SERIAL_PORT = original_serial_port


if __name__ == "__main__":
    unittest.main()
