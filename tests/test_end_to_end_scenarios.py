import importlib.util
import os
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

from database import Database
from main import DoorLockServer
from vision_ai import VisionAI

HAS_FASTAPI_CLIENT = (
    importlib.util.find_spec("fastapi.testclient") is not None
    and importlib.util.find_spec("starlette.testclient") is not None
)

if HAS_FASTAPI_CLIENT:
    from fastapi.testclient import TestClient
    import web_app
else:
    TestClient = None
    web_app = None


@unittest.skipUnless(HAS_FASTAPI_CLIENT, "FastAPI/Starlette TestClient is unavailable")
class TestEndToEndScenarios(unittest.TestCase):
    def setUp(self):
        self.original_db = web_app.db
        self.original_vision = web_app.vision
        self.original_callback = web_app.cmd_callback

        fd, self.db_path = tempfile.mkstemp(prefix="doorlock_e2e_", suffix=".db")
        os.close(fd)
        self.db = Database(db_path=self.db_path)
        self.commands = MagicMock()
        self.web_vision = VisionAI(mock=True)
        web_app.configure_services(
            database=self.db,
            vision_ai=self.web_vision,
            command_callback=self.commands,
        )
        if hasattr(web_app.app.state, "last_capture"):
            del web_app.app.state.last_capture

        self.client = TestClient(web_app.app)

    def tearDown(self):
        self.client.close()
        web_app.configure_services(
            database=self.original_db,
            vision_ai=self.original_vision,
            command_callback=self.original_callback,
        )
        self.web_vision.release()
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = f"{self.db_path}{suffix}"
            if os.path.exists(path):
                os.remove(path)

    def test_gui_pages_expose_required_workflow_controls(self):
        dashboard = self.client.get("/")
        register = self.client.get("/register")
        users = self.client.get("/users_page")

        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("문 열기", dashboard.text)
        self.assertIn("긴급 잠금", dashboard.text)
        self.assertIn("/video_feed", dashboard.text)
        self.assertIn("/api/control/${action}", dashboard.text)

        self.assertEqual(register.status_code, 200)
        self.assertIn("/api/capture_face", register.text)
        self.assertIn("/api/register", register.text)
        self.assertIn("NFC UID", register.text)
        self.assertIn("PIN", register.text)

        self.assertEqual(users.status_code, 200)
        self.assertIn("/api/users", users.text)
        self.assertIn("삭제", users.text)

    def test_video_feed_has_mjpeg_boundary_without_camera(self):
        with patch.object(web_app, "cv2", None):
            chunk = next(web_app.generate_frames())

        self.assertTrue(chunk.startswith(b"--frame\r\n"))
        self.assertIn(b"Content-Type: image/jpeg", chunk)
        self.assertIn(b"\xff\xd8", chunk)

    def test_registration_authentication_logs_and_manual_control_flow(self):
        capture_response = self.client.post("/api/capture_face")
        self.assertEqual(capture_response.status_code, 200)
        self.assertTrue(capture_response.json()["success"])
        self.assertIsInstance(web_app.app.state.last_capture, bytes)

        register_response = self.client.post(
            "/api/register",
            json={"name": "Alice", "nfc_uid": "a1b2c3d4", "password": "1234"},
        )
        self.assertEqual(register_response.status_code, 200)
        self.assertTrue(register_response.json()["success"])
        self.assertIsNone(web_app.app.state.last_capture)

        users_response = self.client.get("/api/users")
        self.assertEqual(users_response.status_code, 200)
        self.assertEqual(users_response.json()[0]["username"], "Alice")
        self.assertEqual(users_response.json()[0]["nfc_uid"], "A1B2C3D4")

        with patch("serial.Serial"):
            server = DoorLockServer(db=self.db, vision=self.web_vision)
        server.ser = MagicMock()
        server.notifier = MagicMock()
        server.rate_limit_seconds = 0
        web_app.configure_services(command_callback=server.send_command)

        server.handle_wakeup("WAKEUP:NFC:a1b2c3d4")
        server.handle_wakeup("WAKEUP:PW:9999")

        self.assertEqual(
            server.ser.write.call_args_list[:2],
            [call(b"OPEN_DOOR\n"), call(b"AUTH_FAIL\n")],
        )

        logs_response = self.client.get("/api/logs")
        self.assertEqual(logs_response.status_code, 200)
        statuses = [entry["status"] for entry in logs_response.json()["logs"]]
        self.assertIn("FINAL_SUCCESS", statuses)
        self.assertIn("UNAUTHORIZED", statuses)

        self.client.post("/api/control/open")
        self.client.post("/api/control/lockdown")

        self.assertEqual(
            server.ser.write.call_args_list[-2:],
            [call(b"OPEN_DOOR\n"), call(b"LOCKDOWN\n")],
        )

        server.vision.release()


if __name__ == "__main__":
    unittest.main()
