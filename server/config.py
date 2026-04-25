import os
from pathlib import Path


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
WEB_HOST = os.getenv("DOORLOCK_WEB_HOST", "0.0.0.0")
WEB_PORT = _int_env("DOORLOCK_WEB_PORT", 8000)
LEGACY_FLASK_PORT = _int_env("DOORLOCK_LEGACY_FLASK_PORT", 5000)
FLASK_DEBUG = _bool_env("DOORLOCK_FLASK_DEBUG", False)
SERIAL_PORT = os.getenv("DOORLOCK_SERIAL_PORT", "/dev/ttyACM0")
BAUD_RATE = _int_env("DOORLOCK_BAUD_RATE", 9600)
SERIAL_RECONNECT_INTERVAL_SECONDS = _float_env("DOORLOCK_SERIAL_RECONNECT_INTERVAL_SECONDS", 5.0)
DISCORD_WEBHOOK_URL = os.getenv("DOORLOCK_DISCORD_WEBHOOK_URL", "")
NOTIFIER_TIMEOUT_SECONDS = _float_env("DOORLOCK_NOTIFIER_TIMEOUT_SECONDS", 5.0)
RATE_LIMIT_SECONDS = _float_env("DOORLOCK_RATE_LIMIT_SECONDS", 3.0)
LOCKDOWN_FAILURE_LIMIT = _int_env("DOORLOCK_LOCKDOWN_FAILURE_LIMIT", 10)
LOCKDOWN_DELAY_SECONDS = _float_env("DOORLOCK_LOCKDOWN_DELAY_SECONDS", 5.0)
LOCKDOWN_ALERT_COOLDOWN_SECONDS = _float_env("DOORLOCK_LOCKDOWN_ALERT_COOLDOWN_SECONDS", 60.0)
DB_BACKUP_INTERVAL_SECONDS = _float_env("DOORLOCK_DB_BACKUP_INTERVAL_SECONDS", 3600.0)

VISION_MOCK = _bool_env("DOORLOCK_VISION_MOCK", False)
ALLOW_UNENROLLED_FACE = _bool_env("DOORLOCK_ALLOW_UNENROLLED_FACE", False)
FACE_MATCH_TOLERANCE = _float_env("DOORLOCK_FACE_TOLERANCE", 0.6)

YOLO_ENABLED = _bool_env("DOORLOCK_YOLO_ENABLED", True)
YOLO_MODEL_PATH = Path(
    os.getenv("DOORLOCK_YOLO_MODEL_PATH", str(PROJECT_ROOT / "models" / "doorlock_yolov8n.pt"))
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
