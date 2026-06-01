import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import MagicMock, call

CURRENT_DIR = Path(__file__).resolve().parent
SERVER_DIR = CURRENT_DIR.parent / "server"
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from database import Database

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


class MockVision:
    def __init__(self):
        self.capture_calls = 0
        self.capture_result = (b"face-encoding", "Face captured successfully.")
        self.reconnect_calls = 0

    def capture_face_encoding(self):
        self.capture_calls += 1
        return self.capture_result

    def reconnect(self):
        self.reconnect_calls += 1
        return True

    def get_status(self):
        return {
            "connected": True,
            "status": "mock",
            "mock": True,
            "source": "mock",
            "backend": "mock",
            "port": None,
            "last_error": None,
            "candidates": [],
        }


@unittest.skipUnless(HAS_FASTAPI_CLIENT, "FastAPI/Starlette TestClient is unavailable")
class TestWebApiDeep(unittest.TestCase):
    def setUp(self):
        self.server = web_app
        self.original_db = self.server.db
        self.original_vision = self.server.vision
        self.original_callback = self.server.cmd_callback
        self.original_doorlock_server = self.server.doorlock_server

        fd, self.db_path = tempfile.mkstemp(prefix="doorlock_api_deep_", suffix=".db")
        os.close(fd)
        self.db = Database(db_path=self.db_path)

        self.mock_vision = MockVision()
        self.mock_callback = MagicMock()
        self.mock_doorlock_server = MagicMock()
        self.mock_doorlock_server.get_serial_status.return_value = {
            "connected": True,
            "status": "connected",
            "port": "/dev/ttyACM_TEST",
            "configured_port": "auto",
            "baud_rate": 9600,
            "last_error": None,
            "candidates": ["/dev/ttyACM_TEST"],
            "last_probe_at": 123.0,
        }
        self.mock_doorlock_server.reconnect_serial.return_value = True
        self.server.configure_services(
            database=self.db,
            vision_ai=self.mock_vision,
            command_callback=self.mock_callback,
            doorlock_server=self.mock_doorlock_server,
        )

        if hasattr(self.server.app.state, "last_capture"):
            del self.server.app.state.last_capture

        self.client = TestClient(self.server.app)

    def tearDown(self):
        self.client.close()
        self.server.configure_services(
            database=self.original_db,
            vision_ai=self.original_vision,
            command_callback=self.original_callback,
            doorlock_server=self.original_doorlock_server,
        )
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = f"{self.db_path}{suffix}"
            if os.path.exists(path):
                os.remove(path)

    def _post_register(self, name, nfc_uid, password):
        payload = {"name": name, "nfc_uid": nfc_uid, "password": password}
        return self.client.post("/api/register", json=payload)

    def test_register_validation_conflict_returns_400(self):
        response = self._post_register(name="Jane", nfc_uid="ZZZZ", password="1234")
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertIn("NFC UID", payload["message"])

    def test_register_duplicate_conflict_returns_409(self):
        self.assertIsNotNone(self.db.add_user("Existing", "A1B2C3D4", "1234"))
        response = self._post_register(name="Another", nfc_uid="A1B2C3D4", password="5678")
        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()["success"])

    def test_users_endpoints_and_delete(self):
        first = self._post_register(name="Alice", nfc_uid="FACE0001", password="0001")
        second = self._post_register(name="Bob", nfc_uid="FACE0002", password="0002")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        users = self.client.get("/api/users").json()
        self.assertEqual(len(users), 2)
        user_ids = {user["id"] for user in users}
        self.assertTrue(user_ids)

        target_id = users[0]["id"]
        delete_response = self.client.delete(f"/api/users/{target_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.json()["success"])

        remaining = self.client.get("/api/users").json()
        self.assertEqual(len(remaining), 1)
        self.assertNotIn(target_id, {u["id"] for u in remaining})

    def test_logs_payload_contains_alert_state(self):
        self.db.log_access(None, "PW", "UNAUTHORIZED", snapshot=b"\x00\x01")
        self.db.log_access(None, "NFC", "UNAUTHORIZED")
        self.db.log_access(None, "PW", "FINAL_FAIL")

        response = self.client.get("/api/logs")
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["alert"])
        self.assertEqual(len(payload["logs"]), 3)
        self.assertEqual(payload["total"], 3)
        self.assertTrue(all("has_snapshot" in entry for entry in payload["logs"]))

    def test_logs_endpoint_respects_limit_and_user_activity(self):
        user_id = self.db.add_user("Activity User", "AA11BB22", "1234")
        self.db.log_access(user_id, "NFC", "1ST_AUTH_SUCCESS")
        self.db.log_access(user_id, "NFC", "FINAL_SUCCESS")
        self.db.log_access(None, "PW", "UNAUTHORIZED")

        limited = self.client.get("/api/logs?limit=2").json()
        self.assertEqual(limited["total"], 3)
        self.assertEqual(len(limited["logs"]), 2)

        activity_response = self.client.get(f"/api/users/{user_id}/activity")
        self.assertEqual(activity_response.status_code, 200)
        activity = activity_response.json()
        self.assertEqual(activity["username"], "Activity User")
        self.assertEqual(activity["stats"]["successful_entries"], 1)
        self.assertEqual(activity["stats"]["total_events"], 2)
        self.assertEqual(len(activity["logs"]), 2)

    def test_logs_snapshot_route_returns_image_or_404(self):
        self.db.log_access(None, "PW", "UNAUTHORIZED", snapshot=b"\xff\xd8jpeg")
        latest = self.db.get_recent_logs(limit=1)[0]
        success_response = self.client.get(f"/api/logs/{latest['id']}/snapshot")

        self.assertEqual(success_response.status_code, 200)
        self.assertEqual(success_response.headers.get("content-type"), "image/jpeg")
        self.assertEqual(success_response.content, b"\xff\xd8jpeg")

        missing_response = self.client.get("/api/logs/999999/snapshot")
        self.assertEqual(missing_response.status_code, 404)

    def test_control_endpoints_forward_callbacks(self):
        open_response = self.client.post("/api/control/open")
        lockdown_response = self.client.post("/api/control/lockdown")

        self.assertEqual(open_response.status_code, 200)
        self.assertEqual(open_response.json()["message"], "Door open command sent.")
        self.assertEqual(lockdown_response.status_code, 200)
        self.assertEqual(lockdown_response.json()["message"], "Lockdown command sent.")

        self.assertEqual(
            self.mock_callback.call_args_list,
            [call("OPEN_DOOR"), call("LOCKDOWN")],
        )

    def test_capture_face_respects_mock_vision(self):
        self.mock_vision.capture_result = (b"abc123", "mocked capture ok")
        response = self.client.post("/api/capture_face")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["message"], "mocked capture ok")
        self.assertEqual(self.server.app.state.last_capture, b"abc123")

        self.mock_vision.capture_result = (None, "capture failed")
        response = self.client.post("/api/capture_face")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["success"])
        self.assertEqual(response.json()["message"], "capture failed")

    def test_status_and_reconnect_endpoints_report_hardware_links(self):
        status_response = self.client.get("/api/status")
        self.assertEqual(status_response.status_code, 200)
        payload = status_response.json()
        self.assertTrue(payload["arduino"]["connected"])
        self.assertEqual(payload["arduino"]["port"], "/dev/ttyACM_TEST")
        self.assertEqual(payload["camera"]["status"], "mock")

        arduino_response = self.client.post("/api/reconnect/arduino")
        camera_response = self.client.post("/api/reconnect/camera")
        all_response = self.client.post("/api/reconnect/all")

        self.assertEqual(arduino_response.status_code, 200)
        self.assertTrue(arduino_response.json()["success"])
        self.assertEqual(camera_response.status_code, 200)
        self.assertTrue(camera_response.json()["success"])
        self.assertEqual(all_response.status_code, 200)
        self.assertTrue(all_response.json()["arduino_success"])
        self.assertTrue(all_response.json()["camera_success"])
        self.assertGreaterEqual(self.mock_doorlock_server.reconnect_serial.call_count, 2)
        self.assertGreaterEqual(self.mock_vision.reconnect_calls, 2)


if __name__ == "__main__":
    unittest.main()
