import serial
import time
import threading
from pathlib import Path
from database import Database
from vision_ai import VisionAI
from notifier import Notifier
from config import (
    BAUD_RATE,
    DB_BACKUP_INTERVAL_SECONDS,
    DISCORD_WEBHOOK_URL,
    LOCKDOWN_ALERT_COOLDOWN_SECONDS,
    LOCKDOWN_DELAY_SECONDS,
    LOCKDOWN_FAILURE_LIMIT,
    RATE_LIMIT_SECONDS,
    SERIAL_RECONNECT_INTERVAL_SECONDS,
    SERIAL_PORT,
    WEB_HOST,
    WEB_PORT,
)

class DoorLockServer:
    def __init__(self, db=None, vision=None):
        self.db = db if db else Database()
        self.vision = vision if vision else VisionAI()
        self.notifier = Notifier(DISCORD_WEBHOOK_URL)
        self.ser = None
        self.last_failed_attempt = 0
        self.last_lockdown_alert = None
        self.rate_limit_seconds = self._min_float(RATE_LIMIT_SECONDS, 0.0)
        self.lockdown_failure_limit = self._min_int(LOCKDOWN_FAILURE_LIMIT, 1)
        self.lockdown_delay_seconds = self._min_float(LOCKDOWN_DELAY_SECONDS, 0.0)
        self.lockdown_alert_cooldown_seconds = self._min_float(LOCKDOWN_ALERT_COOLDOWN_SECONDS, 0.0)
        self.db_backup_interval_seconds = self._min_float(DB_BACKUP_INTERVAL_SECONDS, 1.0)
        self.serial_reconnect_interval_seconds = self._min_float(SERIAL_RECONNECT_INTERVAL_SECONDS, 0.1)
        self.connect_serial()

    @staticmethod
    def _min_float(value, minimum):
        try:
            return max(float(value), minimum)
        except (TypeError, ValueError):
            return minimum

    @staticmethod
    def _min_int(value, minimum):
        try:
            return max(int(value), minimum)
        except (TypeError, ValueError):
            return minimum

    def _redact_auth_value(self, auth_type, value):
        value = str(value or "")
        if auth_type == "NFC" and len(value) > 4:
            return f"...{value[-4:]}"
        return "[REDACTED]"

    def _safe_display_text(self, value, max_length=80):
        text = "".join(" " if ord(char) < 32 else char for char in str(value or "Unknown")).strip()
        if len(text) > max_length:
            return f"{text[:max_length - 3]}..."
        return text or "Unknown"

    def _parse_wakeup_message(self, data):
        if not isinstance(data, str):
            return None

        parts = data.strip().split(":", 2)
        if len(parts) != 3 or parts[0] != "WAKEUP":
            return None

        auth_type = parts[1].strip().upper()
        value = parts[2].strip()
        if auth_type not in {"NFC", "PW"} or not value:
            return None

        return auth_type, value

    def connect_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"Connected to Arduino on {SERIAL_PORT}")
        except Exception as e:
            print(f"Could not connect to Serial: {e}. Retrying in background...")
            self.ser = None

    def shutdown(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception as e:
                print(f"[ERROR] Serial close failed: {e}")
            finally:
                self.ser = None
        self.vision.release()
        self.db.close()

    def send_command(self, cmd):
        if self.ser:
            try:
                self.ser.write(f"{cmd}\n".encode())
            except Exception as e:
                print(f"[ERROR] Serial write failed: {e}")
                self.ser = None
        print(f"[SERVER -> ARDUINO] {cmd}")

    def capture_snapshot(self):
        try:
            import cv2
        except ImportError:
            return None
            
        if self.vision.camera_available and self.vision.camera:
            ret, frame = self.vision.camera.read()
            if ret:
                success, buffer = cv2.imencode('.jpg', frame)
                if success:
                    return buffer.tobytes()
        return None

    def handle_wakeup(self, data):
        now = time.monotonic()
        parsed = self._parse_wakeup_message(data)
        if not parsed:
            return

        # 최근 실패 기록이 너무 많으면 잠시 입력을 무시한다.
        recent_failures = self.db.get_recent_failures_count("ALL")
        if recent_failures >= self.lockdown_failure_limit:
            print("[LOCKDOWN] Too many failed attempts recently. Inputs are paused.")
            if (
                self.last_lockdown_alert is None
                or now - self.last_lockdown_alert >= self.lockdown_alert_cooldown_seconds
            ):
                self.notifier.send_security_alert(
                    f"Doorlock inputs paused\n{self.lockdown_failure_limit}+ failed attempts detected within the last hour."
                )
                self.last_lockdown_alert = now
            time.sleep(self.lockdown_delay_seconds) # 잠시 대기
            return

        # 실패 직후에는 바로 재시도하지 못하게 한다.
        if now - self.last_failed_attempt < self.rate_limit_seconds:
            print(f"[DENIED] Rate limited. Please wait {self.rate_limit_seconds:g} seconds before trying again.")
            return

        auth_type, value = parsed
        user = None

        if auth_type == "NFC":
            user = self.db.verify_nfc(value)
            method = "NFC"
        elif auth_type == "PW":
            user = self.db.verify_password(value)
            method = "PASSWORD"

        if user:
            user_id, username = user
            safe_username = self._safe_display_text(username)
            print(f"[AUTH] {safe_username} verified via {method}. Running face check...")
            self.db.log_access(user_id, method, "1ST_AUTH_SUCCESS")
            
            if self.vision.verify_face(user_id, self.db):
                print(f"[AUTH] Face check passed. Opening door for {safe_username}.")
                self.db.log_access(user_id, method, "FINAL_SUCCESS")
                self.send_command("OPEN_DOOR")
            else:
                self.last_failed_attempt = time.monotonic()
                print(f"[AUTH] Face check failed for {safe_username}.")
                snapshot = self.capture_snapshot()
                self.db.log_access(user_id, method, "FINAL_FAIL", snapshot=snapshot)
                self.notifier.send_security_alert(f"Failed 2FA for registered user: **{safe_username}**", snapshot)
        else:
            self.last_failed_attempt = time.monotonic()
            safe_value = self._redact_auth_value(auth_type, value)
            print(f"[DENIED] Unauthorized {auth_type} attempt: {safe_value}")
            snapshot = self.capture_snapshot()
            self.db.log_access(None, auth_type, "UNAUTHORIZED", snapshot=snapshot)
            self.notifier.send_security_alert(f"Unauthorized **{auth_type}** access attempt: {safe_value}", snapshot)

    def run(self):
        from web_app import configure_services, start_web_server

        # 웹 화면은 메인 시리얼 loop와 분리해서 실행한다.
        configure_services(database=self.db, vision_ai=self.vision)
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        print(f"Web UI started at http://{WEB_HOST}:{WEB_PORT}")

        # 설정된 간격마다 SQLite 백업을 만든다.
        def backup_db_task():
            while True:
                try:
                    db_path = Path(self.db.db_path)
                    suffix = db_path.suffix or ".db"
                    backup_path = db_path.with_name(f"{db_path.stem}_backup{suffix}")
                    self.db.backup_to(backup_path)
                    print(f"[SYSTEM] Database backup completed: {backup_path}")
                except Exception as e:
                    print(f"[ERROR] DB Backup failed: {e}")
                time.sleep(self.db_backup_interval_seconds)
                
        backup_thread = threading.Thread(target=backup_db_task, daemon=True)
        backup_thread.start()

        print("Server is running. Waiting for Wake-up signal...")
        last_reconnect_time = 0
        try:
            while True:
                if self.ser:
                    try:
                        if self.ser.in_waiting > 0:
                            line = self.ser.readline().decode('utf-8').strip()
                            if line.startswith("WAKEUP"):
                                self.handle_wakeup(line)
                    except Exception as e:
                        print(f"[ERROR] Serial read failed: {e}")
                        self.ser = None
                else:
                    # 설정된 간격마다 재연결을 시도한다.
                    current_time = time.monotonic()
                    if current_time - last_reconnect_time > self.serial_reconnect_interval_seconds:
                        self.connect_serial()
                        last_reconnect_time = current_time
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.shutdown()

if __name__ == "__main__":
    server = DoorLockServer()
    server.run()
