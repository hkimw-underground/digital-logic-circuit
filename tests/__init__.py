"""Test package setup for the doorlock project."""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = REPO_ROOT / "server"

if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

os.environ.setdefault("DOORLOCK_VISION_MOCK", "1")
os.environ.setdefault("DOORLOCK_YOLO_ENABLED", "false")
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
