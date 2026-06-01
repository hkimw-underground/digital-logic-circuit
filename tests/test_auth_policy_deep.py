import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

SERVER_DIR = os.path.dirname(__file__)
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from main import DoorLockServer
from database import Database
from vision_ai import VisionAI


class TestAuthPolicyDeep(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("DOORLOCK_VISION_MOCK", "1")

        self._tmpdir = tempfile.TemporaryDirectory(prefix="doorlock-auth-policy-")
        self.addCleanup(self._tmpdir.cleanup)
        self.db_path = os.path.join(self._tmpdir.name, "doorlock.db")
        self.db = Database(db_path=self.db_path)
        self.addCleanup(self.db.close)

        patcher = patch("serial.Serial")
        patcher.start()
        self.addCleanup(patcher.stop)

        self.server = DoorLockServer(db=self.db, vision=VisionAI(mock=True))
        self.server.ser = MagicMock()
        self.server.notifier = MagicMock()
        self.server.lockdown_failure_limit = 3
        self.server.lockdown_delay_seconds = 0.0
        self.server.lockdown_alert_cooldown_seconds = 60.0
        self.server.rate_limit_seconds = 3.0

    def tearDown(self):
        self.server.shutdown()

    def _latest_statuses(self):
        return self.db.get_recent_statuses(limit=5)

    def _register_user(self, username="User", nfc_uid="A1B2C3D4", password="1234"):
        face_encoding, _ = self.server.vision.capture_face_encoding()
        return self.db.add_user(username, nfc_uid=nfc_uid, password=password, face_encoding=face_encoding)

    def test_parse_wakeup_message_cases_and_rejections(self):
        self.assertEqual(self.server._parse_wakeup_message("  WAKEUP:pw:2468  "), ("PW", "2468"))
        self.assertEqual(self.server._parse_wakeup_message("WAKEUP:NFC:A1:B2"), ("NFC", "A1:B2"))
        self.assertIsNone(self.server._parse_wakeup_message("WAKEUP:RFID:9999"))
        self.assertIsNone(self.server._parse_wakeup_message("WAKEUP:NFC:"))
        self.assertIsNone(self.server._parse_wakeup_message("HELLO"))
        self.assertIsNone(self.server._parse_wakeup_message(None))

    def test_successful_nfc_auth_sends_open_and_logs(self):
        self._register_user(username="Alice", nfc_uid="A11B22C3", password="5555")

        self.server.handle_wakeup("WAKEUP:NFC:A11B22C3")

        self.server.ser.write.assert_called_once_with(b"OPEN_DOOR\n")
        self.assertEqual(self._latest_statuses()[:2], ["FINAL_SUCCESS", "1ST_AUTH_SUCCESS"])

        logs = self.db.get_recent_logs(limit=1)
        self.assertEqual(logs[0]["method"], "NFC")

    def test_successful_pin_auth_sends_open_and_logs_password_method(self):
        self._register_user(username="Bob", nfc_uid="B22C33D4", password="2468")

        self.server.handle_wakeup("WAKEUP:PW:2468")

        self.server.ser.write.assert_called_once_with(b"OPEN_DOOR\n")
        logs = self.db.get_recent_logs(limit=1)
        self.assertEqual(logs[0]["method"], "PASSWORD")
        self.assertEqual(logs[0]["status"], "FINAL_SUCCESS")

    def test_unauthorized_nfc_and_pin_commands_send_auth_fail(self):
        self._register_user(username="CardUser", nfc_uid="C33D44E5", password="1357")

        self.server.handle_wakeup("WAKEUP:NFC:UNKNOWN")
        self.server.ser.write.assert_called_once_with(b"AUTH_FAIL\n")
        self.assertEqual(self._latest_statuses()[0], "UNAUTHORIZED")

        with patch.object(self.server, "_parse_wakeup_message", return_value=("PW", "9999")):
            self.server.last_failed_attempt = 0
            self.server.db.get_recent_failures_count = MagicMock(return_value=0)
            self.server.handle_wakeup("whatever")

        self.assertEqual(self.server.ser.write.call_count, 2)
        self.assertEqual(self.server.ser.write.call_args_list[1], unittest.mock.call(b"AUTH_FAIL\n"))
        self.assertEqual(self._latest_statuses()[0], "UNAUTHORIZED")
        self.assertTrue(self.server.notifier.send_security_alert.called)

    def test_face_fail_records_final_fail_and_auth_fail(self):
        user_id = self._register_user(username="FaceFail", nfc_uid="FACE9001", password="9876")
        self.assertIsNotNone(user_id)

        with patch.object(self.server.vision, "verify_face", return_value=False):
            self.server.handle_wakeup("WAKEUP:NFC:FACE9001")

        self.assertEqual(self.server.ser.write.call_args, unittest.mock.call(b"AUTH_FAIL\n"))
        self.assertEqual(self._latest_statuses()[:2], ["FINAL_FAIL", "1ST_AUTH_SUCCESS"])
        self.assertEqual(self.server.notifier.send_security_alert.call_count, 1)
        self.assertEqual(self.db.get_recent_logs(limit=1)[0]["status"], "FINAL_FAIL")

    def test_rate_limit_blocks_retry_before_window_and_allows_at_boundary(self):
        self.server.db.get_recent_failures_count = MagicMock(return_value=0)
        self.server.rate_limit_seconds = 2.5

        timestamps = iter([10.0, 10.0, 12.4, 12.5, 12.5])
        with patch("main.time.monotonic", side_effect=lambda: next(timestamps)):
            self.server.handle_wakeup("WAKEUP:PW:0000")
            self.server.handle_wakeup("WAKEUP:PW:0000")
            self.server.handle_wakeup("WAKEUP:PW:0000")

        self.assertEqual(self.server.ser.write.call_count, 2)
        self.assertEqual(self._latest_statuses()[0], "UNAUTHORIZED")
        self.assertEqual(self._latest_statuses()[:2], ["UNAUTHORIZED", "UNAUTHORIZED"])

    def test_lockdown_threshold_triggers_lockdown_and_cooldown(self):
        self.server.lockdown_failure_limit = 2
        self.server.lockdown_delay_seconds = 0.0
        self.server.lockdown_alert_cooldown_seconds = 5.0
        self.db.log_access(None, "PW", "UNAUTHORIZED")
        self.db.log_access(None, "NFC", "UNAUTHORIZED")

        with patch("main.time.monotonic", side_effect=[100.0, 100.0, 102.0]), patch("main.time.sleep") as mock_sleep:
            self.server.handle_wakeup("WAKEUP:PW:9999")
            self.server.handle_wakeup("WAKEUP:PW:9999")

        self.assertEqual(self.server.ser.write.call_count, 2)
        self.assertEqual(self.server.ser.write.mock_calls, [unittest.mock.call(b"LOCKDOWN\n"), unittest.mock.call(b"LOCKDOWN\n")])
        self.assertEqual(self.server.notifier.send_security_alert.call_count, 1)
        mock_sleep.assert_called_with(0.0)

    def test_lockdown_alert_sends_again_after_cooldown_boundary(self):
        self.server.lockdown_failure_limit = 1
        self.server.lockdown_alert_cooldown_seconds = 10.0
        self.server.lockdown_delay_seconds = 0.0
        self.db.log_access(None, "PW", "UNAUTHORIZED")

        with patch("main.time.monotonic", side_effect=[200.0, 205.0, 210.0]):
            self.server.handle_wakeup("WAKEUP:PW:0000")
            self.server.handle_wakeup("WAKEUP:PW:0000")
            self.server.handle_wakeup("WAKEUP:PW:0000")

        self.assertEqual(self.server.notifier.send_security_alert.call_count, 2)

    def test_malformed_wakeup_messages_are_ignored(self):
        initial_statuses = self._latest_statuses()
        self.server.handle_wakeup("WAKEUP:PW:")
        self.server.handle_wakeup("RANDOM_TEXT")
        self.server.handle_wakeup(None)

        self.assertEqual(self.server.ser.write.call_count, 0)
        self.assertEqual(self.server.notifier.send_security_alert.call_count, 0)
        self.assertEqual(self._latest_statuses(), initial_statuses)


if __name__ == "__main__":
    unittest.main()
