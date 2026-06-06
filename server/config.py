import os
from pathlib import Path


# .env 파일이 있으면 환경변수로 읽어들인다.
def _load_dotenv():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


def _bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _list_env(name, default):
    value = os.getenv(name)
    if value is None:
        return {item.lower() for item in default}
    return {item.strip().lower() for item in value.split(",") if item.strip()}


DB_PATH = Path(os.getenv("DOORLOCK_DB_PATH", str(BASE_DIR / "doorlock.db"))).expanduser()
DATABASE_URL = os.getenv("DOORLOCK_DATABASE_URL", "")
WEB_HOST = os.getenv("DOORLOCK_WEB_HOST", "0.0.0.0")
WEB_PORT = _int_env("DOORLOCK_WEB_PORT", 8000)
LEGACY_FLASK_PORT = _int_env("DOORLOCK_LEGACY_FLASK_PORT", 5000)
FLASK_DEBUG = _bool_env("DOORLOCK_FLASK_DEBUG", False)
CAMERA_URL = os.getenv("DOORLOCK_CAMERA_URL", "0") # "0" 은 기본 웹캠, IP 카메라면 "http://192.168.x.x:81/stream" 등 입력
def _detect_serial_port():
    """기본은 자동 탐지다. 명시 포트가 필요할 때만 DOORLOCK_SERIAL_PORT를 쓴다."""
    env_val = os.getenv("DOORLOCK_SERIAL_PORT")
    if env_val:
        return env_val
    return "auto"


SERIAL_PORT = _detect_serial_port()
BAUD_RATE = _int_env("DOORLOCK_BAUD_RATE", 9600)
ESP32CAM_BAUD_RATE = _int_env("DOORLOCK_ESP32CAM_BAUD_RATE", 2000000)
ESP32CAM_READ_TIMEOUT_SECONDS = _float_env("DOORLOCK_ESP32CAM_READ_TIMEOUT_SECONDS", 1.5)
ESP32CAM_BOOT_WAIT_SECONDS = _float_env("DOORLOCK_ESP32CAM_BOOT_WAIT_SECONDS", 1.5)
SERIAL_RECONNECT_INTERVAL_SECONDS = _float_env("DOORLOCK_SERIAL_RECONNECT_INTERVAL_SECONDS", 5.0)
DISCORD_WEBHOOK_URL = os.getenv("DOORLOCK_DISCORD_WEBHOOK_URL", "")
NOTIFIER_TIMEOUT_SECONDS = _float_env("DOORLOCK_NOTIFIER_TIMEOUT_SECONDS", 5.0)
RATE_LIMIT_SECONDS = _float_env("DOORLOCK_RATE_LIMIT_SECONDS", 3.0)
LOCKDOWN_FAILURE_LIMIT = _int_env("DOORLOCK_LOCKDOWN_FAILURE_LIMIT", 10)
LOCKDOWN_DELAY_SECONDS = _float_env("DOORLOCK_LOCKDOWN_DELAY_SECONDS", 5.0)
LOCKDOWN_ALERT_COOLDOWN_SECONDS = _float_env("DOORLOCK_LOCKDOWN_ALERT_COOLDOWN_SECONDS", 60.0)
DB_BACKUP_INTERVAL_SECONDS = _float_env("DOORLOCK_DB_BACKUP_INTERVAL_SECONDS", 3600.0)

VISION_MOCK = _bool_env("DOORLOCK_VISION_MOCK", False)
MOCK_FACE_IDENTITY = os.getenv("DOORLOCK_MOCK_FACE_IDENTITY", "demo-person")
ALLOW_UNENROLLED_FACE = _bool_env("DOORLOCK_ALLOW_UNENROLLED_FACE", False)
FACE_MATCH_TOLERANCE = _float_env("DOORLOCK_FACE_TOLERANCE", 0.6)
FACE_LIVENESS_REQUIRED = _bool_env("DOORLOCK_FACE_LIVENESS_REQUIRED", True)
ARCFACE_MODEL_PATH = Path(
    os.getenv("DOORLOCK_ARCFACE_MODEL_PATH", str(PROJECT_ROOT / "yolo_vulkan_test" / "models" / "arcface.onnx"))
).expanduser()
ENROLLED_EMBEDDING_DIR = Path(
    os.getenv("DOORLOCK_ENROLLED_EMBEDDING_DIR", str(PROJECT_ROOT / "face_encodings"))
).expanduser()

YOLO_ENABLED = _bool_env("DOORLOCK_YOLO_ENABLED", True)
YOLO_MODEL_PATH = Path(
    os.getenv("DOORLOCK_YOLO_MODEL_PATH", str(PROJECT_ROOT / "yolo_vulkan_test" / "models" / "yolov8s.onnx"))
).expanduser()
YOLO_CONFIDENCE = _float_env("DOORLOCK_YOLO_CONFIDENCE", 0.35)
YOLO_OBSERVATION_SECONDS = _float_env("DOORLOCK_YOLO_OBSERVATION_SECONDS", 4.5)
YOLO_FRAME_INTERVAL_SECONDS = _float_env("DOORLOCK_YOLO_FRAME_INTERVAL_SECONDS", 0.15)
YOLO_CROP_MARGIN = _float_env("DOORLOCK_YOLO_CROP_MARGIN", 0.2)
YOLO_REQUIRE_BLINK = _bool_env("DOORLOCK_YOLO_REQUIRE_BLINK", True)
YOLO_FACE_CLASSES = _list_env("DOORLOCK_YOLO_FACE_CLASSES", {"face"})
YOLO_PHONE_CLASSES = _list_env(
    "DOORLOCK_YOLO_PHONE_CLASSES",
    {"cell phone", "mobile phone", "phone", "smartphone", "screen", "tablet", "laptop", "tv", "monitor"},
)
YOLO_OPEN_EYE_CLASSES = _list_env(
    "DOORLOCK_YOLO_OPEN_EYE_CLASSES",
    {"open_eye", "eye_open", "open eye", "eye open", "open"},
)
YOLO_CLOSED_EYE_CLASSES = _list_env(
    "DOORLOCK_YOLO_CLOSED_EYE_CLASSES",
    {"closed_eye", "eye_closed", "closed eye", "eye closed", "closed"},
)
