import glob
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
        self.serial_port = None
        self.serial_status = "disconnected"
        self.serial_last_error = None
        self.serial_candidates = []
        self.serial_last_probe_at = None
        self.serial_last_activity_at = None
        self._serial_last_healthcheck = 0
        self.serial_lock = threading.RLock()
        self.nfc_capture_lock = threading.RLock()
        self.nfc_capture = {
            "active": False,
            "uid": None,
            "started_at": None,
            "expires_at": None,
            "captured_at": None,
        }
        self.last_failed_attempt = 0
        self.last_lockdown_alert = None
        self.rate_limit_seconds = self._min_float(RATE_LIMIT_SECONDS, 0.0)
        self.lockdown_failure_limit = self._min_int(LOCKDOWN_FAILURE_LIMIT, 1)
        self.lockdown_delay_seconds = self._min_float(LOCKDOWN_DELAY_SECONDS, 0.0)
        self.lockdown_alert_cooldown_seconds = self._min_float(LOCKDOWN_ALERT_COOLDOWN_SECONDS, 0.0)
        self.db_backup_interval_seconds = self._min_float(DB_BACKUP_INTERVAL_SECONDS, 1.0)
        self.serial_reconnect_interval_seconds = self._min_float(SERIAL_RECONNECT_INTERVAL_SECONDS, 0.1)
        self.connect_serial()

    def start_nfc_capture(self, timeout_seconds=15):
        timeout = self._min_float(timeout_seconds, 1.0)
        now = time.time()
        with self.nfc_capture_lock:
            self.nfc_capture = {
                "active": True,
                "uid": None,
                "started_at": now,
                "expires_at": now + timeout,
                "captured_at": None,
            }
            return self.get_nfc_capture_status()

    def get_nfc_capture_status(self):
        now = time.time()
        with self.nfc_capture_lock:
            capture = dict(self.nfc_capture)
            if capture["active"] and capture["expires_at"] and now >= capture["expires_at"]:
                capture["active"] = False
                self.nfc_capture["active"] = False
            remaining = 0
            if capture["active"] and capture["expires_at"]:
                remaining = max(0, int(capture["expires_at"] - now + 0.999))
            capture["remaining_seconds"] = remaining
            return capture

    def _capture_nfc_uid(self, uid):
        now = time.time()
        with self.nfc_capture_lock:
            capture = self.nfc_capture
            if not capture["active"]:
                return False
            if capture["expires_at"] and now >= capture["expires_at"]:
                capture["active"] = False
                return False
            capture["active"] = False
            capture["uid"] = str(uid or "").strip().upper()
            capture["captured_at"] = now
            return True

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

    def _serial_haystack(self, port_info):
        return " ".join(
            str(value or "")
            for value in (
                getattr(port_info, "device", ""),
                getattr(port_info, "description", ""),
                getattr(port_info, "hwid", ""),
                getattr(port_info, "manufacturer", ""),
                getattr(port_info, "product", ""),
            )
        ).lower()

    def _arduino_candidate_score(self, device, haystack=""):
        text = f"{device or ''} {haystack or ''}".lower()
        score = 0
        if "/dev/ttyacm" in text:
            score += 40
        if "/dev/ttyusb" in text:
            score += 5
        if "arduino" in text:
            score += 80
        if "uno r4" in text or "renesas" in text:
            score += 60
        if "cdc" in text or "acm" in text:
            score += 15
        if any(blocked in text for blocked in ("xilinx", "digilent")):
            score -= 1000
        if any(blocked in text for blocked in ("esp32", "ch340", "ch341", "cp210", "usb2.0-serial", "silicon labs", "1a86", "10c4")):
            score -= 200
        return score

    def _serial_port_candidates(self, requested_port=None):
        requested = str(requested_port or SERIAL_PORT or "auto").strip()
        seen = {}
        blocked_devices = set()

        def add_candidate(device, haystack="", explicit=False):
            if not device:
                return
            if not explicit and device in blocked_devices:
                return
            if not explicit and not (device.startswith("/dev/ttyACM") or device.startswith("/dev/ttyUSB")):
                return
            score = self._arduino_candidate_score(device, haystack)
            if not explicit and score <= -500:
                blocked_devices.add(device)
                seen.pop(device, None)
                return
            candidate = {
                "device": device,
                "score": score,
                "explicit": explicit,
                "haystack": haystack,
            }
            existing = seen.get(device)
            if existing is None or candidate["score"] > existing["score"] or explicit:
                seen[device] = candidate

        if requested and requested.lower() != "auto":
            add_candidate(requested, "explicit", explicit=True)

        try:
            from serial.tools import list_ports
            for port_info in list_ports.comports():
                add_candidate(getattr(port_info, "device", None), self._serial_haystack(port_info))
        except Exception:
            pass

        for device in sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*")):
            add_candidate(device)

        candidates = list(seen.values())
        candidates.sort(key=lambda item: (not item["explicit"], -item["score"], item["device"]))
        return candidates

    def _read_probe_response(
        self,
        ser,
        timeout_seconds=1.4,
        allow_legacy_ready=False,
        process_legacy_activity=False,
    ):
        deadline = time.monotonic() + timeout_seconds
        lines = []
        try:
            ser.write(b"PING\n")
            if hasattr(ser, "flush"):
                ser.flush()
        except Exception as e:
            return False, f"probe write failed: {e}", lines

        while time.monotonic() < deadline:
            try:
                raw = ser.readline()
            except Exception as e:
                return False, f"probe read failed: {e}", lines

            if not raw:
                continue
            if not isinstance(raw, (bytes, bytearray)):
                return False, "probe read returned non-bytes", lines

            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            lines.append(line)

            if line == "PONG:DOORLOCK_ARDUINO":
                return True, line, lines
            if allow_legacy_ready and (line == "SYSTEM_READY" or line.startswith("WAKEUP:")):
                if process_legacy_activity and line.startswith("WAKEUP:"):
                    self.handle_wakeup(line)
                return True, f"legacy activity: {line}", lines
            if line.startswith("ESP32CAM_READY") or line.startswith("PONG:READY") or line.startswith("PONG:NOT_READY"):
                return False, "ESP32-CAM responded on this port.", lines

        return False, "no Arduino probe response", lines

    def _close_serial_locked(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception as e:
                print(f"[ERROR] Serial close failed: {e}")
        self.ser = None
        self.serial_port = None

    def _open_arduino_candidate(self, candidate):
        device = candidate["device"]
        explicit = candidate["explicit"]
        try:
            ser = serial.Serial(device, BAUD_RATE, timeout=0.25, write_timeout=0.5)
        except Exception as e:
            return None, str(e)

        if explicit and device.startswith("/dev/pts/"):
            return ser, "explicit PTY test port"

        time.sleep(0.2)
        ok, reason, _lines = self._read_probe_response(ser, timeout_seconds=2.5, allow_legacy_ready=explicit)
        if ok:
            return ser, reason

        if explicit and candidate["score"] > -500:
            # Explicit ports remain supported for older firmware and PTY-based demos.
            return ser, f"explicit port opened without probe match ({reason})"

        try:
            ser.close()
        except Exception:
            pass
        return None, reason

    def connect_serial(self, requested_port=None, force=False):
        with self.serial_lock:
            if self.ser and not force:
                return True
            if force:
                self._close_serial_locked()

            self.serial_status = "scanning"
            self.serial_last_probe_at = time.time()
            candidates = self._serial_port_candidates(requested_port=requested_port)
            self.serial_candidates = [candidate["device"] for candidate in candidates]

            if not candidates:
                self.serial_status = "disconnected"
                self.serial_last_error = "No /dev/ttyACM* or /dev/ttyUSB* candidates found."
                print(f"   Arduino 연결 대기 중... ({SERIAL_PORT}) — {self.serial_last_error}")
                return False

            errors = []
            for candidate in candidates:
                ser, reason = self._open_arduino_candidate(candidate)
                if ser:
                    self.ser = ser
                    self.serial_port = candidate["device"]
                    self.serial_status = "connected"
                    self.serial_last_error = None
                    self.serial_last_activity_at = time.time()
                    self._serial_last_healthcheck = time.monotonic()
                    print(f"\n✅ [성공] Arduino 연결됨: {self.serial_port} @ {BAUD_RATE} ({reason})")
                    print("   이제 키패드/NFC 입력을 받을 수 있습니다.\n")
                    return True
                errors.append(f"{candidate['device']}: {reason}")

            self.ser = None
            self.serial_port = None
            self.serial_status = "disconnected"
            self.serial_last_error = "; ".join(errors[-4:]) or "No Arduino-compatible serial port responded."
            print(f"   Arduino 연결 대기 중... ({SERIAL_PORT}) — {self.serial_last_error}")
            return False

    def reconnect_serial(self):
        return self.connect_serial(force=True)

    def get_serial_status(self):
        with self.serial_lock:
            is_open = bool(self.ser and getattr(self.ser, "is_open", True))
            status = "connected" if is_open else self.serial_status
            return {
                "connected": is_open,
                "status": status,
                "port": self.serial_port if is_open else None,
                "configured_port": SERIAL_PORT,
                "baud_rate": BAUD_RATE,
                "last_error": self.serial_last_error,
                "candidates": list(self.serial_candidates),
                "last_probe_at": self.serial_last_probe_at,
                "last_activity_at": self.serial_last_activity_at,
            }

    def check_serial_health(self):
        with self.serial_lock:
            if not self.ser:
                return False
            if not getattr(self.ser, "is_open", True):
                self._close_serial_locked()
                self.serial_status = "disconnected"
                self.serial_last_error = "Serial port closed."
                return False

            ok, reason, _lines = self._read_probe_response(
                self.ser,
                timeout_seconds=0.6,
                allow_legacy_ready=True,
                process_legacy_activity=True,
            )
            self._serial_last_healthcheck = time.monotonic()
            if ok:
                self.serial_last_error = None
                self.serial_last_activity_at = time.time()
                return True

            self._close_serial_locked()
            self.serial_status = "disconnected"
            self.serial_last_error = f"Serial health check failed: {reason}"
            return False

    def shutdown(self):
        with self.serial_lock:
            self._close_serial_locked()
            self.serial_status = "disconnected"
        self.vision.release()
        self.db.close()

    def send_command(self, cmd):
        with self.serial_lock:
            ser = self.ser
            if ser:
                try:
                    ser.write(f"{cmd}\n".encode())
                except Exception as e:
                    print(f"[ERROR] Serial write failed: {e}")
                    self._close_serial_locked()
                    self.serial_status = "disconnected"
                    self.serial_last_error = str(e)
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
        auth_type, value = parsed

        if auth_type == "NFC" and self._capture_nfc_uid(value):
            print(f"[NFC_CAPTURE] Captured NFC UID for registration: {value}")
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
            self.send_command("LOCKDOWN")
            time.sleep(self.lockdown_delay_seconds) # 잠시 대기
            return

        # 실패 직후에는 바로 재시도하지 못하게 한다.
        if now - self.last_failed_attempt < self.rate_limit_seconds:
            print(f"[DENIED] Rate limited. Please wait {self.rate_limit_seconds:g} seconds before trying again.")
            return

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
                self.send_command("AUTH_FAIL")
                snapshot = self.capture_snapshot()
                self.db.log_access(user_id, method, "FINAL_FAIL", snapshot=snapshot)
                self.notifier.send_security_alert(f"Failed 2FA for registered user: **{safe_username}**", snapshot)
        else:
            self.last_failed_attempt = time.monotonic()
            safe_value = self._redact_auth_value(auth_type, value)
            print(f"[DENIED] Unauthorized {auth_type} attempt: {safe_value}")
            self.send_command("AUTH_FAIL")
            snapshot = self.capture_snapshot()
            self.db.log_access(None, auth_type, "UNAUTHORIZED", snapshot=snapshot)
            self.notifier.send_security_alert(f"Unauthorized **{auth_type}** access attempt: {safe_value}", snapshot)

    def process_serial_once(self):
        with self.serial_lock:
            ser = self.ser
            if not ser:
                return None
            try:
                if ser.in_waiting <= 0:
                    return None
                raw = ser.readline()
            except Exception as e:
                if self.ser is ser:
                    self._close_serial_locked()
                    self.serial_status = "disconnected"
                    self.serial_last_error = str(e)
                return None

        line = raw.decode('utf-8').strip()
        if not line:
            return None
        if line == "SYSTEM_READY":
            print("[ARDUINO] SYSTEM_READY 수신 — 아두이노 부팅 완료, 입력 대기 중")
        elif line.startswith("WAKEUP"):
            self.handle_wakeup(line)
        elif line == "PONG:DOORLOCK_ARDUINO":
            pass
        with self.serial_lock:
            if self.ser is ser:
                self.serial_last_activity_at = time.time()
        return line

    def run(self):
        from web_app import configure_services, start_web_server

        # 웹 화면은 메인 시리얼 loop와 분리해서 실행한다.
        configure_services(
            database=self.db,
            vision_ai=self.vision,
            command_callback=self.send_command,
            doorlock_server=self,
        )
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

        print("Server is running. Waiting for Arduino (SYSTEM_READY or WAKEUP)...")
        print("   [실제 하드웨어] Arduino USB 연결 후 자동 인식됩니다. (/dev/ttyACM* 또는 /dev/ttyUSB*)")
        last_reconnect_time = 0
        try:
            while True:
                if self.ser:
                    try:
                        if not getattr(self.ser, "is_open", True):
                            with self.serial_lock:
                                self._close_serial_locked()
                                self.serial_status = "disconnected"
                                self.serial_last_error = "Serial port closed."
                            continue
                        self.process_serial_once()
                        current_time = time.monotonic()
                        if current_time - self._serial_last_healthcheck > self.serial_reconnect_interval_seconds:
                            self.check_serial_health()
                    except Exception as e:
                        print(f"[ERROR] Serial read failed: {e}")
                        with self.serial_lock:
                            self._close_serial_locked()
                            self.serial_status = "disconnected"
                            self.serial_last_error = str(e)
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
