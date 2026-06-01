import unittest
from unittest.mock import MagicMock, patch

import vision_ai
from vision_ai import SerialJpegCamera, VisionAI


HAS_IMAGE_RUNTIME = (
    not isinstance(vision_ai.cv2, MagicMock)
    and not isinstance(vision_ai.np, MagicMock)
    and vision_ai.cv2 is not None
    and vision_ai.np is not None
)

if HAS_IMAGE_RUNTIME:
    import cv2
    import numpy as np
else:
    cv2 = None
    np = None


class FakeSerial:
    def __init__(self, port=None, *args, **kwargs):
        self.port = port
        self.is_open = True
        self._buffer = bytearray()
        self.writes = []

    def reset_input_buffer(self):
        self._buffer.clear()

    def reset_output_buffer(self):
        pass

    def write(self, data):
        self.writes.append(data)
        if data == b"PING\n":
            self._buffer.extend(b"PONG:READY\n")
            return len(data)
        if data == b"CAPTURE\n":
            image = np.zeros((24, 32, 3), dtype=np.uint8)
            ok, encoded = cv2.imencode(".jpg", image)
            if not ok:
                raise RuntimeError("Could not encode test JPEG")
            jpeg = encoded.tobytes()
            self._buffer.extend(b"NOISE\n")
            self._buffer.extend(f"JPEG:{len(jpeg)}\n".encode("ascii"))
            self._buffer.extend(jpeg)
            self._buffer.extend(b"\nEND\n")
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

    def read(self, size):
        chunk = bytes(self._buffer[:size])
        del self._buffer[:size]
        return chunk

    def close(self):
        self.is_open = False


class NotReadySerial(FakeSerial):
    def write(self, data):
        self.writes.append(data)
        if data == b"PING\n":
            self._buffer.extend(b"PONG:NOT_READY\n")
            return len(data)
        if data == b"CAPTURE\n":
            self._buffer.extend(b"ERR:camera_not_ready\n")
            return len(data)
        return len(data)


@unittest.skipUnless(HAS_IMAGE_RUNTIME, "cv2 and numpy are required")
class TestEsp32SerialCamera(unittest.TestCase):
    def test_serial_jpeg_camera_decodes_capture_protocol(self):
        with patch.object(vision_ai.serial, "Serial", FakeSerial):
            camera = SerialJpegCamera("/dev/ttyUSB_FAKE", boot_wait_seconds=0)

        self.assertTrue(camera.isOpened())
        ok, frame = camera.read()
        self.assertTrue(ok)
        self.assertEqual(frame.shape[:2], (24, 32))
        self.assertEqual(camera.serial.writes[-1], b"CAPTURE\n")
        camera.release()
        self.assertFalse(camera.isOpened())

    def test_vision_ai_uses_serial_camera_url(self):
        with patch.object(vision_ai, "CAMERA_URL", "serial:/dev/ttyUSB_FAKE"), \
                patch.object(vision_ai, "ESP32CAM_BOOT_WAIT_SECONDS", 0), \
                patch.object(vision_ai.serial, "Serial", FakeSerial):
            vision = VisionAI(mock=False)

        self.assertTrue(vision.camera_available)
        ret, frame = vision._read_camera_frame()
        self.assertTrue(ret)
        self.assertEqual(frame.shape[:2], (24, 32))
        vision.release()

    def test_auto_detect_skips_arduino_and_xilinx_and_picks_usb_serial(self):
        arduino = MagicMock(device="/dev/ttyACM0", description="Arduino UNO R4", hwid="Arduino", manufacturer="", product="")
        xilinx = MagicMock(device="/dev/ttyUSB1", description="Xilinx ML Carrier", hwid="Xilinx", manufacturer="", product="")
        ch340 = MagicMock(device="/dev/ttyUSB0", description="USB2.0-Serial CH340", hwid="USB VID:PID=1A86:7523", manufacturer="", product="")

        with patch("serial.tools.list_ports.comports", return_value=[arduino, xilinx, ch340]), \
                patch.object(vision_ai.serial, "Serial", FakeSerial):
            camera = SerialJpegCamera("auto", boot_wait_seconds=0)

        self.assertEqual(camera.port, "/dev/ttyUSB0")
        self.assertTrue(camera.isOpened())
        camera.release()

    def test_auto_detect_keeps_not_ready_esp32_port_but_marks_camera_unavailable(self):
        ch340 = MagicMock(device="/dev/ttyUSB0", description="USB2.0-Serial CH340", hwid="USB VID:PID=1A86:7523", manufacturer="", product="")

        with patch("serial.tools.list_ports.comports", return_value=[ch340]), \
                patch.object(vision_ai.serial, "Serial", NotReadySerial):
            camera = SerialJpegCamera("auto", boot_wait_seconds=0)

        self.assertEqual(camera.port, "/dev/ttyUSB0")
        self.assertFalse(camera.isOpened())
        self.assertIn("not ready", camera.last_error)
        camera.release()


if __name__ == "__main__":
    unittest.main()
