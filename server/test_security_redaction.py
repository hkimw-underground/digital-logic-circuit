import os
import unittest
from unittest.mock import MagicMock, patch

from database import Database
from main import DoorLockServer
from vision_ai import VisionAI


class TestSecurityRedaction(unittest.TestCase):
    def setUp(self):
        self.db_path = "/tmp/doorlock_redaction_test.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(db_path=self.db_path)

        with patch("serial.Serial"):
            self.server = DoorLockServer(db=self.db, vision=VisionAI(mock=True))
        self.server.ser = MagicMock()
        self.server.notifier = MagicMock()

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_unauthorized_password_value_is_redacted_in_alert(self):
        self.server.handle_wakeup("WAKEUP:PW:9999")

        message = self.server.notifier.send_security_alert.call_args.args[0]
        self.assertNotIn("9999", message)
        self.assertIn("[REDACTED]", message)

    def test_unauthorized_password_value_is_redacted_in_console_log(self):
        with patch("builtins.print") as mock_print:
            self.server.handle_wakeup("WAKEUP:PW:9999")

        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list if call.args)
        self.assertNotIn("9999", printed)
        self.assertIn("[REDACTED]", printed)

    def test_unauthorized_nfc_value_only_keeps_suffix_in_alert(self):
        self.server.handle_wakeup("WAKEUP:NFC:A1B2C3D4")

        message = self.server.notifier.send_security_alert.call_args.args[0]
        self.assertNotIn("A1B2C3D4", message)
        self.assertIn("...C3D4", message)

    def test_registered_username_is_sanitized_for_alerts(self):
        user_id = self.db.add_user("Bad\nName", nfc_uid="FACE9999", password="1234")
        self.assertIsNotNone(user_id)

        with patch.object(self.server.vision, "verify_face", return_value=False):
            self.server.handle_wakeup("WAKEUP:NFC:FACE9999")

        message = self.server.notifier.send_security_alert.call_args.args[0]
        self.assertNotIn("\n", message)
        self.assertIn("Bad Name", message)

    def test_lockdown_alert_uses_cooldown(self):
        self.server.db.get_recent_failures_count = MagicMock(return_value=1)
        self.server.lockdown_failure_limit = 1
        self.server.lockdown_delay_seconds = 0
        self.server.lockdown_alert_cooldown_seconds = 60

        with patch("main.time.monotonic", side_effect=[100, 110]), patch("main.time.sleep"):
            self.server.handle_wakeup("WAKEUP:PW:1111")
            self.server.handle_wakeup("WAKEUP:PW:1111")

        self.assertEqual(self.server.notifier.send_security_alert.call_count, 1)

    def test_malformed_wakeup_message_is_ignored(self):
        self.server.handle_wakeup("WAKEUP:PW:")

        self.server.notifier.send_security_alert.assert_not_called()
        self.server.ser.write.assert_not_called()
        self.assertEqual(self.db.get_recent_logs(limit=1), [])

    def test_malformed_wakeup_message_is_ignored_during_lockdown(self):
        self.server.db.get_recent_failures_count = MagicMock(return_value=99)
        self.server.lockdown_failure_limit = 1
        self.server.lockdown_delay_seconds = 0

        with patch("main.time.sleep") as mock_sleep:
            self.server.handle_wakeup("WAKEUP:PW:")

        self.server.notifier.send_security_alert.assert_not_called()
        mock_sleep.assert_not_called()

    def test_wakeup_parser_normalizes_auth_type_and_preserves_value(self):
        self.assertEqual(
            self.server._parse_wakeup_message("  WAKEUP:pw:1234  "),
            ("PW", "1234"),
        )
        self.assertEqual(
            self.server._parse_wakeup_message("WAKEUP:NFC:A1:B2"),
            ("NFC", "A1:B2"),
        )

    def test_runtime_policy_values_are_clamped(self):
        self.assertEqual(self.server._min_float(-1, 0.0), 0.0)
        self.assertEqual(self.server._min_float("bad", 0.1), 0.1)
        self.assertEqual(self.server._min_float(5, 0.1), 5.0)
        self.assertEqual(self.server._min_int(0, 1), 1)
        self.assertEqual(self.server._min_int("bad", 1), 1)
        self.assertEqual(self.server._min_int(10, 1), 10)

    def test_shutdown_closes_serial_vision_and_database(self):
        serial_mock = MagicMock()
        self.server.ser = serial_mock
        self.server.vision.release = MagicMock()

        self.server.shutdown()

        serial_mock.close.assert_called_once()
        self.server.vision.release.assert_called_once()
        self.assertIsNone(self.server.ser)
        self.assertIsNone(self.db.conn)


if __name__ == "__main__":
    unittest.main()
