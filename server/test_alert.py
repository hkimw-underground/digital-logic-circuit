import os
import unittest

from database import Database


class TestDashboardAlert(unittest.TestCase):
    def setUp(self):
        self.db_path = "/tmp/doorlock_alert_test.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_three_consecutive_failures_trigger_alert(self):
        self.db.log_access(None, "NFC", "UNAUTHORIZED")
        self.db.log_access(None, "PW", "UNAUTHORIZED")
        self.db.log_access(None, "NFC", "UNAUTHORIZED")

        self.assertTrue(self.db.has_consecutive_failures(limit=3))

    def test_user_delete_keeps_access_logs(self):
        user_id = self.db.add_user("DeleteMe", nfc_uid="DELETE01", password="1234")
        self.db.log_access(user_id, "NFC", "FINAL_SUCCESS")

        self.assertTrue(self.db.delete_user(user_id))

        logs = self.db.get_recent_logs(limit=1)
        self.assertEqual(logs[0]["username"], "Unknown")

    def test_nfc_uid_is_normalized_for_storage_and_lookup(self):
        user_id = self.db.add_user("NfcUser", nfc_uid="a1b2c3d4", password="1234")

        self.assertIsNotNone(user_id)
        user = self.db.verify_nfc("A1B2C3D4")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "NfcUser")

    def test_recent_failures_count_can_filter_by_method(self):
        self.db.log_access(None, "NFC", "UNAUTHORIZED")
        self.db.log_access(None, "PW", "UNAUTHORIZED")
        self.db.log_access(None, "PW", "FINAL_SUCCESS")

        self.assertEqual(self.db.get_recent_failures_count("ALL"), 2)
        self.assertEqual(self.db.get_recent_failures_count("NFC"), 1)
        self.assertEqual(self.db.get_recent_failures_count("PW"), 1)

    def test_recent_logs_limit_is_bounded(self):
        self.db.log_access(None, "NFC", "UNAUTHORIZED")
        self.db.log_access(None, "PW", "UNAUTHORIZED")

        self.assertEqual(len(self.db.get_recent_logs(limit=-1)), 2)
        self.assertEqual(len(self.db.get_recent_logs(limit="bad")), 2)
        self.assertEqual(len(self.db.get_recent_statuses(limit=0)), 2)

    def test_consecutive_failures_ignore_first_factor_success_markers(self):
        user_id = self.db.add_user("AlertUser", nfc_uid="FACE01", password="1234")
        for _ in range(3):
            self.db.log_access(user_id, "NFC", "1ST_AUTH_SUCCESS")
            self.db.log_access(user_id, "NFC", "FINAL_FAIL")

        self.assertTrue(self.db.has_consecutive_failures(limit=3))

    def test_successful_terminal_status_breaks_consecutive_failures(self):
        self.db.log_access(None, "PW", "UNAUTHORIZED")
        self.db.log_access(None, "NFC", "FINAL_SUCCESS")
        self.db.log_access(None, "PW", "UNAUTHORIZED")

        self.assertFalse(self.db.has_consecutive_failures(limit=3))

    def test_schema_column_lookup_rejects_unknown_tables(self):
        with self.assertRaises(ValueError):
            self.db._columns("users; DROP TABLE users")

    def test_corrupt_bcrypt_password_hash_fails_closed(self):
        cursor = self.db.conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, nfc_uid, password) VALUES (?, ?, ?)",
            ("CorruptHash", "BADHASH", "$2b$not-a-valid-bcrypt-hash"),
        )
        self.db.conn.commit()

        self.assertIsNone(self.db.verify_password("1234"))

    def test_plaintext_password_is_no_longer_supported(self):
        cursor = self.db.conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, nfc_uid, password) VALUES (?, ?, ?)",
            ("LegacyUser", "LEGACY01", "1234"),
        )
        self.db.conn.commit()

        user = self.db.verify_password("1234")

        self.assertIsNone(user)

    def test_close_is_idempotent(self):
        self.db.close()
        self.db.close()
        self.assertIsNone(self.db.conn)

    def test_queries_after_close_raise_clear_error(self):
        self.db.close()

        with self.assertRaisesRegex(RuntimeError, "Database connection is closed"):
            self.db.get_recent_logs()

    def test_operational_indexes_are_created(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
        indexes = {row[0] for row in cursor.fetchall()}

        self.assertIn("idx_access_logs_user_id", indexes)
        self.assertIn("idx_access_logs_status_id", indexes)
        self.assertIn("idx_access_logs_timestamp", indexes)


if __name__ == "__main__":
    unittest.main()
