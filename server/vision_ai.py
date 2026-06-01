import hashlib
import time
from dataclasses import dataclass

from config import (
    ALLOW_UNENROLLED_FACE,
    CAMERA_URL,
    ESP32CAM_BAUD_RATE,
    ESP32CAM_BOOT_WAIT_SECONDS,
    ESP32CAM_READ_TIMEOUT_SECONDS,
    FACE_LIVENESS_REQUIRED,
    FACE_MATCH_TOLERANCE,
    MOCK_FACE_IDENTITY,
    VISION_MOCK,
    YOLO_CLOSED_EYE_CLASSES,
    YOLO_CONFIDENCE,
    YOLO_CROP_MARGIN,
    YOLO_ENABLED,
    YOLO_FACE_CLASSES,
    YOLO_FRAME_INTERVAL_SECONDS,
    YOLO_MODEL_PATH,
    YOLO_OBSERVATION_SECONDS,
    YOLO_OPEN_EYE_CLASSES,
    YOLO_PHONE_CLASSES,
    YOLO_REQUIRE_BLINK,
)

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import face_recognition
except ImportError:
    face_recognition = None

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    import serial
except ImportError:
    serial = None


class SerialJpegCamera:
    """ESP32-CAM USB-serial JPEG source."""

    def __init__(self, port, baud_rate=921600, timeout_seconds=4.0, boot_wait_seconds=1.5):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout_seconds = timeout_seconds
        self.boot_wait_seconds = boot_wait_seconds
        self.serial = None
        self.last_error = None
        self.candidates = []
        self.device_ready = True

        if serial is None:
            self.last_error = "pyserial is not installed."
            return
        if cv2 is None or np is None:
            self.last_error = "OpenCV and numpy are required for ESP32-CAM serial JPEG."
            return

        try:
            if str(port).lower() == "auto":
                port = self._auto_detect_port()
                if not port:
                    self.last_error = "No ESP32-CAM USB-serial candidate found. Check /dev/serial/by-id."
                    return
                self.port = port
            self.serial = serial.Serial(
                port,
                baud_rate,
                timeout=timeout_seconds,
                write_timeout=timeout_seconds,
            )
            if boot_wait_seconds > 0:
                time.sleep(boot_wait_seconds)
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
        except Exception as e:
            self.last_error = str(e)
            self.serial = None

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

    def _esp32_candidate_score(self, device, haystack=""):
        text = f"{device or ''} {haystack or ''}".lower()
        score = 0
        if "/dev/ttyusb" in text:
            score += 30
        if "/dev/ttyacm" in text:
            score += 5
        if any(keyword in text for keyword in ("esp32", "ch340", "ch341", "cp210", "usb serial", "usb2.0-serial", "uart", "silicon labs", "1a86", "10c4")):
            score += 80
        if any(blocked in text for blocked in ("arduino", "uno r4", "renesas", "xilinx", "digilent")):
            score -= 1000
        return score

    def _esp32_candidate_ports(self):
        try:
            from serial.tools import list_ports
        except Exception:
            list_ports = None

        seen = {}
        blocked_devices = set()

        def add_candidate(device, haystack=""):
            if not device or not (device.startswith("/dev/ttyUSB") or device.startswith("/dev/ttyACM")):
                return
            if device in blocked_devices:
                return
            score = self._esp32_candidate_score(device, haystack)
            if score <= -500:
                blocked_devices.add(device)
                seen.pop(device, None)
                return
            existing = seen.get(device)
            if existing is None or score > existing["score"]:
                seen[device] = {"device": device, "score": score, "haystack": haystack}

        if list_ports:
            for port_info in list_ports.comports():
                add_candidate(getattr(port_info, "device", None), self._serial_haystack(port_info))

        try:
            import glob
            for device in sorted(glob.glob("/dev/ttyUSB*")) + sorted(glob.glob("/dev/ttyACM*")):
                add_candidate(device)
        except Exception:
            pass

        candidates = list(seen.values())
        candidates.sort(key=lambda item: (-item["score"], item["device"]))
        return candidates

    def _probe_esp32cam(self, port):
        probe_serial = None
        try:
            probe_serial = serial.Serial(
                port,
                self.baud_rate,
                timeout=0.25,
                write_timeout=0.5,
            )
            if self.boot_wait_seconds > 0:
                time.sleep(min(self.boot_wait_seconds, 1.5))
            probe_serial.write(b"PING\n")
            probe_serial.flush()
            deadline = time.monotonic() + 1.2
            while time.monotonic() < deadline:
                raw = probe_serial.readline()
                if not raw:
                    continue
                if not isinstance(raw, (bytes, bytearray)):
                    return False, "probe read returned non-bytes"
                line = raw.decode("ascii", errors="ignore").strip()
                if not line:
                    continue
                if line.startswith("PONG:READY") or line.startswith("ESP32CAM_READY"):
                    return True, line
                if line.startswith("PONG:NOT_READY"):
                    return True, line
                if line == "PONG:DOORLOCK_ARDUINO" or line == "SYSTEM_READY":
                    return False, "Arduino responded on this port."
            return False, "no ESP32-CAM probe response"
        except Exception as e:
            return False, str(e)
        finally:
            if probe_serial:
                try:
                    probe_serial.close()
                except Exception:
                    pass

    def _auto_detect_port(self):
        self.candidates = []
        candidates = self._esp32_candidate_ports()
        self.candidates = [candidate["device"] for candidate in candidates]
        for candidate in candidates:
            ok, reason = self._probe_esp32cam(candidate["device"])
            if ok:
                self.device_ready = not str(reason).startswith("PONG:NOT_READY")
                if not self.device_ready:
                    self.last_error = f"{candidate['device']}: ESP32-CAM responded but camera is not ready ({reason})."
                return candidate["device"]
            self.last_error = f"{candidate['device']}: {reason}"
        return None

    def isOpened(self):
        return bool(self.serial and self.serial.is_open and self.device_ready)

    def _read_jpeg_payload(self):
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            header = self.serial.readline().decode("ascii", errors="ignore").strip()
            if not header:
                continue
            if header.startswith("ERR:"):
                self.last_error = header
                return None
            if not header.startswith("JPEG:"):
                continue
            try:
                length = int(header.split(":", 1)[1])
            except ValueError:
                self.last_error = f"Invalid JPEG header: {header}"
                return None
            if length <= 0 or length > 500000:
                self.last_error = f"Invalid JPEG length: {length}"
                return None

            payload = bytearray()
            while len(payload) < length and time.monotonic() < deadline:
                chunk = self.serial.read(length - len(payload))
                if chunk:
                    payload.extend(chunk)
            if len(payload) != length:
                self.last_error = f"Incomplete JPEG payload: {len(payload)}/{length}"
                return None
            return bytes(payload)

        self.last_error = "Timed out waiting for JPEG header."
        return None

    def read(self):
        if self.serial and self.serial.is_open and not self.device_ready:
            self.last_error = self.last_error or "ESP32-CAM responded but camera is not ready."
            return False, None
        if not self.isOpened():
            return False, None

        try:
            self.serial.reset_input_buffer()
            self.serial.write(b"CAPTURE\n")
            self.serial.flush()
            jpeg = self._read_jpeg_payload()
            if not jpeg:
                return False, None

            frame = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                self.last_error = "OpenCV could not decode ESP32-CAM JPEG."
                return False, None
            return True, frame
        except Exception as e:
            self.last_error = str(e)
            return False, None

    def release(self):
        if self.serial:
            try:
                self.serial.close()
            except Exception:
                pass
        self.serial = None


@dataclass
class YoloDetection:
    label: str
    confidence: float
    box: tuple

    @property
    def area(self):
        x1, y1, x2, y2 = self.box
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


@dataclass
class YoloSecurityResult:
    ok: bool
    face_crop: object = None
    reason: str = ""
    blink_detected: bool = False
    phone_detected: bool = False


class VisionAI:
    FACE_ENCODING_PREFIX = b"FACE128F64:"
    FACE_ENCODING_SIZE = 128

    def __init__(self, mock=None):
        self.mock = VISION_MOCK if mock is None else mock
        self.camera = None
        self.camera_available = False
        self.camera_source = str(CAMERA_URL)
        self.camera_backend = "mock" if self.mock else "none"
        self.camera_last_error = None
        self.yolo_model = None
        self.yolo_model_loaded = False
        self.yolo_model_error = None
        self.yolo_enabled = YOLO_ENABLED
        self.yolo_model_path = YOLO_MODEL_PATH
        self.yolo_confidence = YOLO_CONFIDENCE
        self.yolo_observation_seconds = YOLO_OBSERVATION_SECONDS
        self.yolo_frame_interval_seconds = YOLO_FRAME_INTERVAL_SECONDS
        self.yolo_crop_margin = YOLO_CROP_MARGIN
        self.yolo_require_blink = YOLO_REQUIRE_BLINK
        self.yolo_face_classes = self._normalize_classes(YOLO_FACE_CLASSES)
        self.yolo_phone_classes = self._normalize_classes(YOLO_PHONE_CLASSES)
        self.yolo_open_eye_classes = self._normalize_classes(YOLO_OPEN_EYE_CLASSES)
        self.yolo_closed_eye_classes = self._normalize_classes(YOLO_CLOSED_EYE_CLASSES)
        self.mock_face_identity = str(MOCK_FACE_IDENTITY or "demo-person")

        if self.mock:
            print("[VISION] Explicit mock mode enabled by configuration.")
        else:
            self._open_camera()
            
        self.blink_threshold = 0.2
        self.required_blinks = 1

    def _normalize_label(self, label):
        return " ".join(str(label).replace("_", " ").replace("-", " ").split()).lower()

    def _normalize_classes(self, labels):
        return {self._normalize_label(label) for label in labels}

    def _label_matches(self, label, expected_labels):
        return self._normalize_label(label) in expected_labels

    def _is_serial_camera_url(self, camera_url):
        return str(camera_url).startswith(("serial:", "esp32cam:", "esp32cam-serial:"))

    def _serial_camera_port(self, camera_url):
        value = str(camera_url)
        if value.startswith(("serial:", "esp32cam:", "esp32cam-serial:")):
            return value.split(":", 1)[1]
        return value

    def _open_camera(self):
        self.camera = None
        self.camera_available = False
        self.camera_last_error = None

        if cv2 is None:
            self.camera_backend = "opencv-missing"
            self.camera_last_error = "OpenCV is not installed."
            print("[VISION] OpenCV not installed. Vision checks will fail closed.")
            return False

        try:
            if self._is_serial_camera_url(self.camera_source):
                port = self._serial_camera_port(self.camera_source)
                self.camera_backend = "esp32cam-serial"
                self.camera = SerialJpegCamera(
                    port,
                    baud_rate=ESP32CAM_BAUD_RATE,
                    timeout_seconds=ESP32CAM_READ_TIMEOUT_SECONDS,
                    boot_wait_seconds=ESP32CAM_BOOT_WAIT_SECONDS,
                )
                if not self.camera.isOpened():
                    self.camera_last_error = self.camera.last_error
                    print(f"[VISION] ESP32-CAM serial camera unavailable on {port}: {self.camera_last_error}")
                    return False
                print(f"[VISION] ESP32-CAM serial camera connected: {self.camera.port} @ {ESP32CAM_BAUD_RATE}")
                self.camera_available = True
                return True

            self.camera_backend = "opencv"
            cam_source = int(self.camera_source) if self.camera_source.isdigit() else self.camera_source
            self.camera = cv2.VideoCapture(cam_source)
            if not self.camera.isOpened():
                self.camera_last_error = "Camera resource busy or not found."
                print("[VISION] Camera resource busy or not found. Check if another app (zoom, browser) is using it.")
                return False
            self.camera_available = True
            return True
        except Exception as e:
            self.camera_last_error = str(e)
            print(f"[VISION] Fatal error opening camera: {e}")
            self.camera_available = False
            return False

    def reconnect(self, camera_url=None):
        if camera_url is not None:
            self.camera_source = str(camera_url)
        if self.mock:
            return True
        if self.camera:
            self.camera.release()
        return self._open_camera()

    def get_status(self):
        if self.mock:
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

        port = None
        candidates = []
        last_error = self.camera_last_error
        if isinstance(self.camera, SerialJpegCamera):
            port = self.camera.port
            candidates = list(self.camera.candidates)
            last_error = self.camera.last_error or last_error

        is_open = bool(self.camera_available and self.camera and self.camera.isOpened())
        return {
            "connected": is_open,
            "status": "connected" if is_open else "disconnected",
            "mock": False,
            "source": self.camera_source,
            "backend": self.camera_backend,
            "port": port,
            "last_error": last_error,
            "candidates": candidates,
        }

    def set_mock_face_identity(self, identity):
        self.mock_face_identity = str(identity or "demo-person")

    def _mock_face_encoding(self):
        if np is None:
            raise RuntimeError("numpy is required for mock face encodings.")

        seed = hashlib.sha256(self.mock_face_identity.encode("utf-8")).digest()
        raw = bytearray()
        counter = 0
        expected_bytes = self.FACE_ENCODING_SIZE * 8
        while len(raw) < expected_bytes:
            raw.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
            counter += 1

        values = np.frombuffer(bytes(raw[:expected_bytes]), dtype=np.uint64).astype(np.float64)
        return (values / np.iinfo(np.uint64).max) - 0.5

    def _load_yolo_model(self):
        if not self.yolo_enabled:
            return False
        if self.yolo_model_loaded:
            return self.yolo_model is not None

        self.yolo_model_loaded = True
        if YOLO is None:
            self.yolo_model_error = "ultralytics is not installed."
            print(f"[VISION] YOLO gate unavailable: {self.yolo_model_error}")
            return False

        model_path = self.yolo_model_path
        explicit_path = model_path.is_absolute() or len(model_path.parts) > 1
        if explicit_path and not model_path.exists():
            self.yolo_model_error = f"YOLO model not found at {model_path}"
            print(f"[VISION] YOLO gate unavailable: {self.yolo_model_error}")
            return False

        try:
            self.yolo_model = YOLO(str(model_path))
            print(f"[VISION] YOLO nano security gate loaded: {model_path}")
            return True
        except Exception as e:
            self.yolo_model_error = str(e)
            print(f"[VISION] YOLO gate failed to load: {e}")
            return False

    def calculate_ear(self, eye_points):
        A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
        B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
        C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
        if C == 0:
            return 0
        return (A + B) / (2.0 * C)

    def _read_camera_frame(self):
        if not self.camera_available or not self.camera:
            return False, None
        return self.camera.read()

    def detect_liveness(self):
        if self.mock:
            return True
        if not self.camera_available:
            print("[VISION] Liveness check unavailable because camera is not ready.")
            return False
        if not face_recognition or np is None:
            print("[VISION] Liveness check unavailable because face_recognition/numpy is missing.")
            return False

        print("[VISION] Checking liveness (Blink detection)...")
        start_time = cv2.getTickCount()
        blink_detected = False
        
        while (cv2.getTickCount() - start_time) / cv2.getTickFrequency() < 5:
            ret, frame = self._read_camera_frame()
            if not ret: break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_landmarks_list = face_recognition.face_landmarks(rgb_frame)
            for face_landmarks in face_landmarks_list:
                left_eye = face_landmarks.get('left_eye')
                right_eye = face_landmarks.get('right_eye')
                if not left_eye or not right_eye:
                    continue
                ear = (self.calculate_ear(left_eye) + self.calculate_ear(right_eye)) / 2.0
                if ear < self.blink_threshold:
                    blink_detected = True
                    break
            if blink_detected: break
        return blink_detected

    def _to_list(self, value):
        if value is None:
            return []
        if hasattr(value, "detach"):
            value = value.detach().cpu()
        if hasattr(value, "tolist"):
            return value.tolist()
        return list(value)

    def _to_float(self, value):
        if hasattr(value, "item"):
            return float(value.item())
        return float(value)

    def _class_label(self, names, class_id):
        if isinstance(names, dict):
            return str(names.get(class_id, class_id))
        if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
            return str(names[class_id])
        return str(class_id)

    def _parse_yolo_result(self, result):
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return []

        xyxy_values = self._to_list(getattr(boxes, "xyxy", []))
        class_values = self._to_list(getattr(boxes, "cls", []))
        confidence_values = self._to_list(getattr(boxes, "conf", []))
        names = getattr(result, "names", None) or getattr(self.yolo_model, "names", {})
        detections = []

        for coords, cls_value, conf_value in zip(xyxy_values, class_values, confidence_values):
            confidence = self._to_float(conf_value)
            if confidence < self.yolo_confidence:
                continue
            class_id = int(self._to_float(cls_value))
            x1, y1, x2, y2 = [float(value) for value in coords[:4]]
            detections.append(
                YoloDetection(
                    label=self._class_label(names, class_id),
                    confidence=confidence,
                    box=(x1, y1, x2, y2),
                )
            )

        return detections

    def _analyze_frame_with_yolo(self, frame):
        if not self._load_yolo_model():
            return None

        try:
            results = self.yolo_model.predict(frame, conf=self.yolo_confidence, verbose=False)
        except Exception as e:
            self.yolo_model_error = str(e)
            print(f"[VISION] YOLO inference failed: {e}")
            return None

        if not results:
            return []
        return self._parse_yolo_result(results[0])

    def _has_presentation_device(self, detections):
        return any(self._label_matches(detection.label, self.yolo_phone_classes) for detection in detections)

    def _pick_best_face(self, detections):
        face_detections = [
            detection for detection in detections
            if self._label_matches(detection.label, self.yolo_face_classes)
        ]
        if not face_detections:
            return None
        return max(face_detections, key=lambda detection: (detection.confidence, detection.area))

    def _detect_eye_state(self, detections):
        has_closed = any(self._label_matches(detection.label, self.yolo_closed_eye_classes) for detection in detections)
        has_open = any(self._label_matches(detection.label, self.yolo_open_eye_classes) for detection in detections)
        if has_closed:
            return "closed"
        if has_open:
            return "open"
        return None

    def _advance_blink_state(self, state, eye_state):
        if state == "done":
            return state, True
        if state == "waiting_open" and eye_state == "open":
            return "waiting_closed", False
        if state == "waiting_closed" and eye_state == "closed":
            return "waiting_reopen", False
        if state == "waiting_reopen" and eye_state == "open":
            return "done", True
        return state, False

    def _crop_frame(self, frame, box):
        if frame is None or not hasattr(frame, "shape"):
            return None

        height, width = frame.shape[:2]
        x1, y1, x2, y2 = box
        margin_x = (x2 - x1) * self.yolo_crop_margin
        margin_y = (y2 - y1) * self.yolo_crop_margin
        left = max(0, int(x1 - margin_x))
        top = max(0, int(y1 - margin_y))
        right = min(width, int(x2 + margin_x))
        bottom = min(height, int(y2 + margin_y))

        if right <= left or bottom <= top:
            return None
        return frame[top:bottom, left:right]

    def _run_yolo_security_gate(self, require_blink=True):
        if not self._load_yolo_model():
            reason = self.yolo_model_error or "YOLO model is unavailable."
            return YoloSecurityResult(ok=False, reason=reason)

        deadline = time.monotonic() + self.yolo_observation_seconds
        blink_state = "waiting_open"
        blink_detected = not require_blink
        best_face_crop = None
        best_face_score = -1.0
        last_reason = "No usable face crop was detected."

        print("[VISION] Running YOLO nano gate (face/device/blink)...")
        while time.monotonic() < deadline:
            ret, frame = self._read_camera_frame()
            if not ret:
                last_reason = "Camera frame read failed during YOLO gate."
                time.sleep(self.yolo_frame_interval_seconds)
                continue

            detections = self._analyze_frame_with_yolo(frame)
            if detections is None:
                return YoloSecurityResult(ok=False, reason=self.yolo_model_error or "YOLO inference failed.")

            if self._has_presentation_device(detections):
                return YoloSecurityResult(
                    ok=False,
                    reason="Phone/screen-like presentation device detected.",
                    phone_detected=True,
                )

            face_detection = self._pick_best_face(detections)
            if face_detection:
                face_crop = self._crop_frame(frame, face_detection.box)
                if face_crop is not None:
                    score = face_detection.confidence * max(1.0, face_detection.area)
                    if score > best_face_score:
                        best_face_score = score
                        best_face_crop = face_crop
                    last_reason = "Blink was not observed in the YOLO window."

            if require_blink:
                eye_state = self._detect_eye_state(detections)
                blink_state, blink_detected = self._advance_blink_state(blink_state, eye_state)

            if best_face_crop is not None and blink_detected:
                return YoloSecurityResult(
                    ok=True,
                    face_crop=best_face_crop,
                    reason="YOLO gate passed.",
                    blink_detected=blink_detected,
                )

            time.sleep(self.yolo_frame_interval_seconds)

        return YoloSecurityResult(ok=False, face_crop=best_face_crop, reason=last_reason, blink_detected=blink_detected)

    def _extract_face_encodings(self, image):
        if not face_recognition or cv2 is None:
            return []
        if image is None or not hasattr(image, "shape"):
            return []

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        try:
            face_locations = face_recognition.face_locations(rgb_image)
            encodings = face_recognition.face_encodings(rgb_image, face_locations)
        except Exception as e:
            print(f"[VISION] Face encoding failed: {e}")
            return []

        if encodings:
            return encodings

        height, width = image.shape[:2]
        if height <= 0 or width <= 0:
            return []
        try:
            return face_recognition.face_encodings(rgb_image, [(0, width, height, 0)])
        except Exception:
            return []

    def _serialize_face_encoding(self, encoding):
        if np is None:
            raise RuntimeError("numpy is required to serialize face encodings.")
        array = np.asarray(encoding, dtype=np.float64)
        if array.shape != (self.FACE_ENCODING_SIZE,):
            raise ValueError("Face encoding must contain 128 values.")
        return self.FACE_ENCODING_PREFIX + array.tobytes()

    def _deserialize_face_encoding(self, encoding_bytes):
        if np is None:
            raise RuntimeError("numpy is required to deserialize face encodings.")
        if not encoding_bytes:
            raise ValueError("Empty face encoding.")

        if encoding_bytes.startswith(self.FACE_ENCODING_PREFIX):
            raw = encoding_bytes[len(self.FACE_ENCODING_PREFIX):]
            expected_bytes = self.FACE_ENCODING_SIZE * np.dtype(np.float64).itemsize
            if len(raw) != expected_bytes:
                raise ValueError("Invalid face encoding length.")
            return np.frombuffer(raw, dtype=np.float64).copy()

        raise ValueError("Invalid or legacy face encoding format detected. Pickle is no longer supported.")

    def capture_face_encoding(self):
        if self.mock:
            try:
                return self._serialize_face_encoding(self._mock_face_encoding()), "Mock face captured successfully."
            except Exception as e:
                return None, f"Mock face capture failed: {e}"
        if not self.camera_available:
            return None, "Camera not available."
        if not face_recognition:
            return None, "face_recognition is not installed."

        frame = None
        if self.yolo_enabled:
            gate_result = self._run_yolo_security_gate(require_blink=False)
            if not gate_result.ok:
                return None, gate_result.reason
            frame = gate_result.face_crop
        else:
            ret, frame = self._read_camera_frame()
            if not ret:
                return None, "Failed to capture frame."

        encodings = self._extract_face_encodings(frame)
        if not encodings:
            return None, "No face detected in the cropped image. Try again."

        return self._serialize_face_encoding(encodings[0]), "Face captured successfully."

    def verify_face(self, user_id, db):
        if self.mock:
            stored_encoding_bytes = db.get_face_encoding(user_id)
            if not stored_encoding_bytes:
                if ALLOW_UNENROLLED_FACE:
                    print(f"[MOCK] No face encoding for user {user_id}. Allowed by DOORLOCK_ALLOW_UNENROLLED_FACE.")
                    return True
                print(f"[MOCK] No face encoding found for user {user_id}. Access denied.")
                return False

            try:
                stored_encoding = self._deserialize_face_encoding(stored_encoding_bytes)
                current_encoding = self._mock_face_encoding()
            except Exception as e:
                print(f"[MOCK] Face encoding is invalid: {e}")
                return False

            verified = np.linalg.norm(stored_encoding - current_encoding) <= FACE_MATCH_TOLERANCE

            if verified:
                print(f"[MOCK] Face verified for user {user_id}")
                return True

            print(f"[MOCK] Face verification failed for user {user_id}")
            return False

        stored_encoding_bytes = db.get_face_encoding(user_id)
        if not stored_encoding_bytes:
            if ALLOW_UNENROLLED_FACE:
                print(f"[VISION] No face encoding for user {user_id}. Allowed by DOORLOCK_ALLOW_UNENROLLED_FACE.")
                return True
            print(f"[VISION] No face encoding found for user {user_id}. Access denied.")
            return False

        if not self.camera_available:
            print("[VISION] Face verification failed because camera is not ready.")
            return False
        if not face_recognition:
            print("[VISION] Face verification failed because face_recognition is missing.")
            return False

        face_frame = None
        if self.yolo_enabled:
            gate_result = self._run_yolo_security_gate(require_blink=self.yolo_require_blink)
            if not gate_result.ok:
                print(f"[VISION] YOLO security gate failed: {gate_result.reason}")
                return False
            face_frame = gate_result.face_crop
        elif FACE_LIVENESS_REQUIRED and not self.detect_liveness():
            print("[VISION] Liveness check failed.")
            return False

        try:
            stored_encoding = self._deserialize_face_encoding(stored_encoding_bytes)
        except Exception as e:
            print(f"[VISION] Stored face encoding is invalid: {e}")
            return False

        if face_frame is None:
            ret, face_frame = self._read_camera_frame()
            if not ret:
                return False

            # YOLO로 얼굴을 자르지 못한 경우에만 전체 프레임을 줄인다.
            face_frame = cv2.resize(face_frame, (0, 0), fx=0.25, fy=0.25)

        face_encodings = self._extract_face_encodings(face_frame)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                [stored_encoding],
                face_encoding,
                tolerance=FACE_MATCH_TOLERANCE,
            )
            if True in matches:
                print(f"[VISION] Face verified for user {user_id}")
                return True
        
        print(f"[VISION] Face verification failed for user {user_id}")
        return False

    def release(self):
        if self.camera:
            self.camera.release()
        self.camera = None
        self.camera_available = False
