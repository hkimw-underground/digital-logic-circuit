import importlib.util
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from database import Database
from vision_ai import VisionAI
import vision_ai

HAS_FACE_RUNTIME = (
    importlib.util.find_spec("numpy") is not None
    and not isinstance(vision_ai.face_recognition, MagicMock)
    and not isinstance(vision_ai.cv2, MagicMock)
)

if HAS_FACE_RUNTIME:
    import numpy as np
else:
    np = None


class FakeCamera:
    def __init__(self, frame):
        self.frame = frame
        self.released = False

    def read(self):
        return True, self.frame.copy()

    def release(self):
        self.released = True


@unittest.skipUnless(HAS_FACE_RUNTIME, "real cv2, numpy, and face_recognition are required")
class TestFaceAuthRuntime(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(prefix="doorlock_face_runtime_", suffix=".db")
        os.close(fd)
        self.db = Database(db_path=self.db_path)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            path = f"{self.db_path}{suffix}"
            if os.path.exists(path):
                os.remove(path)

    def _vision_with_frame(self):
        vision = VisionAI(mock=True)
        vision.mock = False
        vision.yolo_enabled = False
        vision.camera_available = True
        vision.camera = FakeCamera(np.zeros((120, 160, 3), dtype=np.uint8))
        return vision

    def test_registered_face_encoding_can_pass_and_fail_matching(self):
        vision = self._vision_with_frame()
        stored = np.linspace(0.0, 1.0, VisionAI.FACE_ENCODING_SIZE, dtype=np.float64)
        user_id = self.db.add_user(
            "FaceUser",
            nfc_uid="FACE0001",
            password="1234",
            face_encoding=vision._serialize_face_encoding(stored),
        )
        self.assertIsNotNone(user_id)

        with patch.object(vision, "detect_liveness", return_value=True), \
                patch.object(vision, "_extract_face_encodings", return_value=[stored.copy()]):
            self.assertTrue(vision.verify_face(user_id, self.db))

        mismatch = stored + 10.0
        with patch.object(vision, "detect_liveness", return_value=True), \
                patch.object(vision, "_extract_face_encodings", return_value=[mismatch]):
            self.assertFalse(vision.verify_face(user_id, self.db))

        vision.release()

    def test_capture_face_encoding_stores_serializable_128_float_vector(self):
        vision = self._vision_with_frame()
        captured = np.ones(VisionAI.FACE_ENCODING_SIZE, dtype=np.float64)

        with patch.object(vision, "_extract_face_encodings", return_value=[captured.copy()]):
            payload, message = vision.capture_face_encoding()

        self.assertEqual(message, "Face captured successfully.")
        decoded = vision._deserialize_face_encoding(payload)
        np.testing.assert_array_equal(decoded, captured)
        vision.release()


if __name__ == "__main__":
    unittest.main()
