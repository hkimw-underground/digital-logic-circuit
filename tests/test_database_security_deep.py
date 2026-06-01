import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
import shutil
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database import Database


class TestDatabaseSecurityDeep(unittest.TestCase):
    def setUp(self):
        self.work_dir = tempfile.mkdtemp(prefix="doorlock_security_deep_")
        self.db_path = os.path.join(self.work_dir, "doorlock.db")
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.work_dir, ignore_errors=True)

    def _insert_access_log(self, user_id, method, status, snapshot=None, timestamp=None):
        cursor = self.db.conn.cursor()
        cursor.execute(
            "INSERT INTO access_logs (user_id, timestamp, method, status, snapshot) VALUES (?, ?, ?, ?, ?)",
            (user_id, timestamp or datetime.now().isoformat(timespec="seconds"), method, status, snapshot),
        )
        self.db.conn.commit()
        return cursor.lastrowid

    def test_nfc_normalization_and_uid_uniqueness(self):
        user_id = self.db.add_user("Alice", nfc_uid="  a1b2c3d4  ", password="1234")
        self.assertIsNotNone(user_id)
        self.assertIsNotNone(self.db.verify_nfc("A1B2C3D4"))
        self.assertIsNotNone(self.db.verify_nfc("a1b2c3d4"))
        self.assertEqual(self.db.verify_nfc("a1b2c3d4")["id"], user_id)

        duplicate_id = self.db.add_user("Duplicate", nfc_uid="A1B2C3D4", password="5678")
        self.assertIsNone(duplicate_id)

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE nfc_uid = ?", ("A1B2C3D4",))
        self.assertEqual(cursor.fetchone()[0], 1)

    def test_verify_password_uses_bcrypt_only(self):
        user_id = self.db.add_user("BcryptUser", nfc_uid="BEEFCAFE", password="1234")
        self.assertIsNotNone(user_id)

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
        stored_hash = cursor.fetchone()[0]
        self.assertTrue(stored_hash.startswith("$2"))

        self.assertEqual(self.db.verify_password("1234")[0], user_id)
        self.assertIsNone(self.db.verify_password("0000"))

        cursor.execute("UPDATE users SET password = ? WHERE id = ?", ("1234", user_id))
        self.db.conn.commit()
        self.assertIsNone(self.db.verify_password("1234"))

        cursor.execute("UPDATE users SET password = ? WHERE id = ?", ("$2b$not-a-valid-bcrypt-hash", user_id))
        self.db.conn.commit()
        self.assertIsNone(self.db.verify_password("1234"))

    def test_delete_user_preserves_access_logs(self):
        user_id = self.db.add_user("KeepLogs", nfc_uid="KEEPLOGS", password="1234")
        other_user_id = self.db.add_user("Other", nfc_uid="OTHER01", password="1234")

        removed_log = self._insert_access_log(user_id, "NFC", "FINAL_SUCCESS")
        removed_followup_log = self._insert_access_log(user_id, "NFC", "FINAL_FAIL")
        other_log = self._insert_access_log(other_user_id, "PW", "FINAL_SUCCESS")

        self.assertTrue(self.db.delete_user(user_id))

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT user_id FROM access_logs WHERE id IN (?, ?, ?)", (removed_log, removed_followup_log, other_log))
        preserved_users = {row[0] for row in cursor.fetchall()}
        self.assertIn(None, preserved_users)
        self.assertIn(other_user_id, preserved_users)
        self.assertEqual(len(preserved_users), 2)

        logs = self.db.get_recent_logs(limit=3)
        log_usernames = {log["id"]: log["username"] for log in logs}
        self.assertEqual(log_usernames[removed_log], "Unknown")
        self.assertEqual(log_usernames[removed_followup_log], "Unknown")
        self.assertEqual(log_usernames[other_log], "Other")

    def test_recent_failures_count_respects_window_and_method_filter(self):
        now = datetime.now().replace(microsecond=0)
        self._insert_access_log(
            None,
            "NFC",
            "UNAUTHORIZED",
            timestamp=(now - timedelta(hours=2)).isoformat(timespec="seconds"),
        )
        self._insert_access_log(None, "NFC", "FINAL_SUCCESS", timestamp=(now - timedelta(minutes=30)).isoformat(timespec="seconds"))
        self._insert_access_log(None, "NFC", "UNAUTHORIZED", timestamp=(now - timedelta(minutes=10)).isoformat(timespec="seconds"))
        self._insert_access_log(None, "PW", "FINAL_FAIL", timestamp=(now - timedelta(minutes=5)).isoformat(timespec="seconds"))
        self._insert_access_log(None, "PW", "FINAL_SUCCESS", timestamp=(now - timedelta(minutes=1)).isoformat(timespec="seconds"))

        self.assertEqual(self.db.get_recent_failures_count(), 2)
        self.assertEqual(self.db.get_recent_failures_count("NFC"), 1)
        self.assertEqual(self.db.get_recent_failures_count("PW"), 1)
        self.assertEqual(self.db.get_recent_failures_count("NONE"), 0)

    def test_backup_to_honors_permissions_and_path_checks(self):
        self.db.add_user("Backup", nfc_uid="BACKUP01", password="1234")
        self.db.log_access(None, "NFC", "FINAL_SUCCESS")

        backup_path = os.path.join(self.work_dir, "nested", "copy.db")
        created_path = self.db.backup_to(backup_path)

        self.assertEqual(created_path, backup_path)
        self.assertTrue(os.path.exists(backup_path))
        mode = os.stat(backup_path).st_mode & 0o777
        self.assertEqual(mode, 0o600)

        backup = sqlite3.connect(backup_path)
        try:
            cursor = backup.cursor()
            cursor.execute("SELECT username FROM users WHERE nfc_uid = ?", ("BACKUP01",))
            self.assertEqual(cursor.fetchone()[0], "Backup")
        finally:
            backup.close()

        with self.assertRaises(ValueError):
            self.db.backup_to(self.db_path)

    def test_get_log_snapshot(self):
        snapshot = b"binary-snapshot-data"
        log_id = self._insert_access_log(None, "NFC", "UNAUTHORIZED", snapshot=snapshot)

        self.assertEqual(self.db.get_log_snapshot(log_id), snapshot)
        self.assertIsNone(self.db.get_log_snapshot(log_id + 1))

    def test_methods_fail_cleanly_when_connection_closed(self):
        self.db.close()

        with self.assertRaisesRegex(RuntimeError, "Database connection is closed."):
            self.db.verify_nfc("ANY")
        with self.assertRaisesRegex(RuntimeError, "Database connection is closed."):
            self.db.verify_password("1234")
        with self.assertRaisesRegex(RuntimeError, "Database connection is closed."):
            self.db.get_recent_logs()
        with self.assertRaisesRegex(RuntimeError, "Database connection is closed."):
            self.db.get_recent_failures_count()
        with self.assertRaisesRegex(RuntimeError, "Database connection is closed."):
            self.db.get_log_snapshot(1)
        with self.assertRaisesRegex(RuntimeError, "Database connection is closed."):
            self.db.get_recent_statuses()
        with self.assertRaisesRegex(RuntimeError, "Database connection is closed."):
            self.db.backup_to(os.path.join(self.work_dir, "denied.db"))

        with self.assertRaisesRegex(RuntimeError, "Database connection is closed."):
            self.db.add_user("AfterClose", "AFTERCLOSE", "1234")

    def test_log_retrieval_limits_are_bounded(self):
        now = datetime.now().replace(microsecond=0)
        cursor = self.db.conn.cursor()
        for offset in range(150):
            cursor.execute(
                "INSERT INTO access_logs (user_id, timestamp, method, status, snapshot) VALUES (?, ?, ?, ?, ?)",
                (None, (now - timedelta(seconds=offset)).isoformat(timespec="seconds"), "PW", "UNAUTHORIZED", None),
            )
        self.db.conn.commit()

        self.assertEqual(len(self.db.get_recent_logs(limit=500)), 100)
        self.assertEqual(len(self.db.get_recent_logs(limit=0)), 20)
        self.assertEqual(len(self.db.get_recent_logs(limit="bad")), 20)

        self.assertEqual(len(self.db.get_recent_statuses(limit=5000)), 50)
        self.assertEqual(len(self.db.get_recent_statuses(limit=0)), 3)
        self.assertEqual(len(self.db.get_recent_statuses(limit="bad")), 3)


if __name__ == "__main__":
    unittest.main()
