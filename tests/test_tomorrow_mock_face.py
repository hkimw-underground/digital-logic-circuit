import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

try:
    import face_recognition
except Exception:
    face_recognition = MagicMock()

from database import Database
from tools.tomorrow_live_check import MockFaceVision


class TomorrowMockFaceTest(unittest.TestCase):
    def test_mock_face_capture_and_verify_uses_stored_encoding(self):
        if isinstance(face_recognition, MagicMock):
            self.skipTest("face_recognition is not installed in this Python environment")

        with tempfile.TemporaryDirectory(prefix="doorlock-test-mock-face-") as tmp:
            db = Database(db_path=str(Path(tmp) / "doorlock.db"))
            vision = MockFaceVision()
            try:
                encoding, message = vision.capture_face_encoding()
                self.assertIn("Mock face captured", message)
                self.assertIsInstance(encoding, bytes)

                user_id = db.add_user(
                    "MockFaceUser",
                    nfc_uid="ABCD1234",
                    password="1234",
                    face_encoding=encoding,
                )
                self.assertTrue(vision.verify_face(user_id, db))

                no_face_user_id = db.add_user("NoFaceUser", nfc_uid="BEEF1234", password="4321")
                self.assertFalse(vision.verify_face(no_face_user_id, db))

                wrong_encoding = vision.codec._serialize_face_encoding(vision.encoding + 1.0)
                wrong_face_user_id = db.add_user(
                    "WrongFaceUser",
                    nfc_uid="CAFE1234",
                    password="5678",
                    face_encoding=wrong_encoding,
                )
                self.assertFalse(vision.verify_face(wrong_face_user_id, db))
            finally:
                vision.release()
                db.close()


if __name__ == "__main__":
    unittest.main()
