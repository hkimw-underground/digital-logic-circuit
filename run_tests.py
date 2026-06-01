import sys
from unittest.mock import MagicMock

# Do NOT mock bcrypt — DB tests need real password hashing
for module_name in ("serial", "cv2", "requests", "face_recognition", "ultralytics"):
    try:
        __import__(module_name)
    except Exception:
        sys.modules[module_name] = MagicMock()
# Note: fastapi/uvicorn/pydantic are NOT globally mocked here.
# This allows real import checks in test_dashboard_api.py and similar.
# Heavy vision/hardware mocks are still applied above.

import unittest
import os
from pathlib import Path

if __name__ == '__main__':
    repo_root = Path(__file__).resolve().parent
    server_dir = repo_root / 'server'
    if str(server_dir) not in sys.path:
        sys.path.insert(0, str(server_dir))

    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test*.py')
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
