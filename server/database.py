import hmac
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import bcrypt

from config import DB_PATH
from validation import normalize_nfc_uid


class Database:
    _KNOWN_TABLES = {"users", "access_logs"}

    def __init__(self, db_name=None, db_path=None):
        self.db_path = self._resolve_db_path(db_name, db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=20)
        self.conn.row_factory = sqlite3.Row
        self._configure_connection()
        self.create_tables()
        self._secure_file_permissions()

    def _resolve_db_path(self, db_name=None, db_path=None):
        if db_path:
            return str(Path(db_path).expanduser())
        if db_name:
            candidate = Path(db_name).expanduser()
            if candidate.is_absolute():
                return str(candidate)
            return str(Path(__file__).resolve().parent / candidate)
        return str(DB_PATH)

    def _configure_connection(self):
        with self.lock:
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA busy_timeout = 20000")
            self.conn.execute("PRAGMA journal_mode = WAL")

    def _secure_file_permissions(self):
        for path in (self.db_path, f"{self.db_path}-wal", f"{self.db_path}-shm"):
            if os.path.exists(path):
                os.chmod(path, 0o600)

    def _columns(self, table):
        if table not in self._KNOWN_TABLES:
            raise ValueError(f"Unknown table: {table}")
        self._ensure_open()
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return {row["name"] for row in cursor.fetchall()}

    def _ensure_open(self):
        if self.conn is None:
            raise RuntimeError("Database connection is closed.")

    def _bounded_limit(self, limit, default=20, maximum=100):
        try:
            value = int(limit)
        except (TypeError, ValueError):
            return default
        if value < 1:
            return default
        return min(value, maximum)

    def create_tables(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    nfc_uid TEXT UNIQUE,
                    password TEXT,
                    face_encoding BLOB
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    timestamp DATETIME,
                    method TEXT,
                    status TEXT,
                    snapshot BLOB,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            self._migrate_users_table()
            self._migrate_logs_table()
            self._create_indexes()
            self.conn.commit()

    def _migrate_users_table(self):
        columns = self._columns("users")
        cursor = self.conn.cursor()
        if "username" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
            columns.add("username")
        if "name" in columns:
            cursor.execute("UPDATE users SET username = COALESCE(username, name)")
        if "nfc_uid" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN nfc_uid TEXT")
        if "password" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN password TEXT")
        if "face_encoding" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN face_encoding BLOB")

    def _migrate_logs_table(self):
        columns = self._columns("access_logs")
        if "snapshot" not in columns:
            self.conn.execute("ALTER TABLE access_logs ADD COLUMN snapshot BLOB")

    def _create_indexes(self):
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_status_id ON access_logs(status, id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp ON access_logs(timestamp)")

    def add_user(self, username, nfc_uid=None, password=None, face_encoding=None):
        try:
            self._ensure_open()
            nfc_uid = normalize_nfc_uid(nfc_uid)
            hashed_password = None
            if password:
                password = str(password)
                hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, nfc_uid, password, face_encoding) VALUES (?, ?, ?, ?)",
                    (username, nfc_uid, hashed_password, face_encoding),
                )
                self.conn.commit()
                self._secure_file_permissions()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_face_encoding(self, user_id):
        self._ensure_open()
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT face_encoding FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
        return result["face_encoding"] if result else None

    def verify_nfc(self, uid):
        self._ensure_open()
        uid = normalize_nfc_uid(uid)
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, username FROM users WHERE nfc_uid = ?', (uid,))
            return cursor.fetchone()

    def verify_password(self, password):
        self._ensure_open()
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, username, password FROM users WHERE password IS NOT NULL')
            users = cursor.fetchall()
        
        for user_id, username, hashed_password in users:
            if self._matches_password(user_id, password, hashed_password):
                return (user_id, username)
        return None

    def _matches_password(self, user_id, password, stored_password):
        if not stored_password:
            return False

        password = str(password or "")
        if stored_password.startswith(("$2a$", "$2b$", "$2y$")):
            try:
                return bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8"))
            except ValueError:
                return False

        if hmac.compare_digest(password, stored_password):
            self._upgrade_plaintext_password(user_id, password)
            return True
        return False

    def _upgrade_plaintext_password(self, user_id, password):
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
            self.conn.commit()
            self._secure_file_permissions()

    def get_all_users(self):
        self._ensure_open()
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, username, nfc_uid FROM users')
            return cursor.fetchall()

    def delete_user(self, user_id):
        try:
            self._ensure_open()
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('UPDATE access_logs SET user_id = NULL WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                self.conn.commit()
                self._secure_file_permissions()
            return True
        except Exception as e:
            print(f"[DB Delete Error] {e}")
            return False

    def log_access(self, user_id, method, status, snapshot=None):
        try:
            self._ensure_open()
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('INSERT INTO access_logs (user_id, timestamp, method, status, snapshot) VALUES (?, ?, ?, ?, ?)',
                               (user_id, datetime.now().isoformat(timespec="seconds"), method, status, snapshot))
                self.conn.commit()
                self._secure_file_permissions()
        except sqlite3.OperationalError as e:
            print(f"[DB Log Error] {e}")

    def get_recent_logs(self, limit=20):
        self._ensure_open()
        limit = self._bounded_limit(limit)
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT l.id, l.timestamp, COALESCE(u.username, 'Unknown') AS username,
                       l.method, l.status,
                       CASE WHEN l.snapshot IS NOT NULL THEN 1 ELSE 0 END AS has_snapshot
                FROM access_logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.id DESC
                LIMIT ?
            ''', (limit,))
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "username": row["username"],
                    "method": row["method"],
                    "status": row["status"],
                    "has_snapshot": bool(row["has_snapshot"]),
                }
                for row in cursor.fetchall()
            ]

    def get_recent_statuses(self, limit=3):
        self._ensure_open()
        limit = self._bounded_limit(limit, default=3, maximum=50)
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT status FROM access_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [row["status"] for row in cursor.fetchall()]

    def get_recent_terminal_statuses(self, limit=3):
        self._ensure_open()
        limit = self._bounded_limit(limit, default=3, maximum=50)
        terminal_statuses = ("FINAL_SUCCESS", "FINAL_FAIL", "UNAUTHORIZED")
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT status FROM access_logs
                WHERE status IN (?, ?, ?)
                ORDER BY id DESC
                LIMIT ?
                """,
                (*terminal_statuses, limit),
            )
            return [row["status"] for row in cursor.fetchall()]

    def has_consecutive_failures(self, limit=3):
        statuses = self.get_recent_terminal_statuses(limit)
        if len(statuses) < limit:
            return False
        failure_statuses = {"UNAUTHORIZED", "FINAL_FAIL"}
        return all(status in failure_statuses for status in statuses)

    def get_log_snapshot(self, log_id):
        self._ensure_open()
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT snapshot FROM access_logs WHERE id = ?', (log_id,))
            result = cursor.fetchone()
        return result["snapshot"] if result else None

    def get_recent_failures_count(self, method_value="ALL"):
        self._ensure_open()
        params = []
        method_filter = ""
        if method_value and method_value != "ALL":
            method_filter = "AND method = ?"
            params.append(method_value)

        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(f'''
                SELECT COUNT(*) FROM access_logs 
                WHERE status IN ('UNAUTHORIZED', 'FINAL_FAIL') 
                AND datetime(timestamp) >= datetime('now', 'localtime', '-1 hour')
                {method_filter}
            ''', params)
            return cursor.fetchone()[0]

    def backup_to(self, backup_path):
        self._ensure_open()
        backup_path = Path(backup_path).expanduser()
        if Path(self.db_path).expanduser().resolve() == backup_path.resolve():
            raise ValueError("Backup path must be different from the source database path.")
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with self.lock:
            destination = sqlite3.connect(str(backup_path), timeout=20)
            try:
                self.conn.backup(destination)
                destination.commit()
            finally:
                destination.close()

        os.chmod(backup_path, 0o600)
        return str(backup_path)

    def close(self):
        with self.lock:
            if self.conn is not None:
                self.conn.close()
                self.conn = None

if __name__ == "__main__":
    db = Database()
    try:
        print(f"Database ready: {db.db_path}")
    finally:
        db.close()
