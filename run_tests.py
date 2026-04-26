import sys
from unittest.mock import MagicMock

sys.modules['bcrypt'] = MagicMock()
sys.modules['serial'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['face_recognition'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['ultralytics'] = MagicMock()
sys.modules['fastapi'] = MagicMock()
sys.modules['uvicorn'] = MagicMock()
sys.modules['fastapi.responses'] = MagicMock()
sys.modules['fastapi.staticfiles'] = MagicMock()
sys.modules['fastapi.templating'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['multipart'] = MagicMock()

import unittest
import os

if __name__ == '__main__':
    loader = unittest.TestLoader()
    start_dir = 'server'
    suite = loader.discover(start_dir, pattern='test*.py')
    runner = unittest.TextTestRunner()
    runner.run(suite)
