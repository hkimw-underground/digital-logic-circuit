import os
import sqlite3
import stat
import unittest

from database import Database


class TestDatabaseBackup(unittest.TestCase):
    def setUp(self):
        self.db_path = "/tmp/doorlock_backup_source.db"
        self.backup_path = "/tmp/doorlock/backups/doorlock_backup_copy.db"
        for path in (self.db_path, self.backup_path):
            if os.path.exists(path):
                os.remove(path)
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        self.db.close()
        for path in (self.db_path, self.backup_path):
            if os.path.exists(path):
                os.remove(path)

    def test_backup_to_creates_consistent_sqlite_copy(self):
        user_id = self.db.add_user("BackupUser", nfc_uid="BACKUP01", password="1234")
        self.db.log_access(user_id, "NFC", "FINAL_SUCCESS")

        created_path = self.db.backup_to(self.backup_path)

        self.assertEqual(created_path, self.backup_path)
        self.assertTrue(os.path.exists(self.backup_path))
        mode = stat.S_IMODE(os.stat(self.backup_path).st_mode)
        self.assertEqual(mode, 0o600)

        backup = sqlite3.connect(self.backup_path)
        try:
            cursor = backup.cursor()
            cursor.execute("SELECT username FROM users WHERE nfc_uid = ?", ("BACKUP01",))
            self.assertEqual(cursor.fetchone()[0], "BackupUser")
            cursor.execute("SELECT status FROM access_logs ORDER BY id DESC LIMIT 1")
            self.assertEqual(cursor.fetchone()[0], "FINAL_SUCCESS")
        finally:
            backup.close()

    def test_database_and_sqlite_sidecars_are_private_when_present(self):
        self.db.add_user("PrivateFiles", nfc_uid="ABCD1234", password="1234")
        self.db.log_access(None, "NFC", "UNAUTHORIZED")

        for path in (self.db_path, f"{self.db_path}-wal", f"{self.db_path}-shm"):
            if not os.path.exists(path):
                continue
            mode = stat.S_IMODE(os.stat(path).st_mode)
            self.assertEqual(mode, 0o600)

    def test_backup_to_rejects_source_database_path(self):
        with self.assertRaises(ValueError):
            self.db.backup_to(self.db_path)


if __name__ == "__main__":
    unittest.main()
