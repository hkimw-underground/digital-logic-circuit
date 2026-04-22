import unittest
import pickle
from unittest.mock import patch

import numpy as np

from vision_ai import VisionAI, YoloDetection


class FakeCamera:
    def __init__(self, frame):
        self.frame = frame
        self.released = False

    def read(self):
        return True, self.frame.copy()

    def release(self):
        self.released = True


class TestVisionYoloGate(unittest.TestCase):
    def make_vision(self):
        vision = VisionAI(mock=True)
        vision.mock = False
        vision.camera_available = True
        vision.camera = FakeCamera(np.zeros((120, 160, 3), dtype=np.uint8))
        vision.yolo_enabled = True
        vision.yolo_model = object()
        vision.yolo_model_loaded = True
        vision.yolo_observation_seconds = 1
        vision.yolo_frame_interval_seconds = 0
        return vision

    def test_yolo_gate_passes_after_face_and_blink_transition(self):
        vision = self.make_vision()
        sequence = [
            [
                YoloDetection("face", 0.92, (40, 20, 100, 90)),
                YoloDetection("open_eye", 0.88, (52, 42, 62, 48)),
            ],
            [
                YoloDetection("face", 0.93, (40, 20, 100, 90)),
                YoloDetection("closed_eye", 0.9, (52, 42, 62, 48)),
            ],
            [
                YoloDetection("face", 0.94, (40, 20, 100, 90)),
                YoloDetection("open_eye", 0.89, (52, 42, 62, 48)),
            ],
        ]

        def analyze(_frame):
            return sequence.pop(0)

        vision._analyze_frame_with_yolo = analyze

        result = vision._run_yolo_security_gate(require_blink=True)

        self.assertTrue(result.ok)
        self.assertTrue(result.blink_detected)
        self.assertIsNotNone(result.face_crop)
        self.assertEqual(result.face_crop.shape[:2], (98, 84))

    def test_yolo_gate_rejects_phone_screen_detection(self):
        vision = self.make_vision()
        vision._analyze_frame_with_yolo = lambda _frame: [
            YoloDetection("face", 0.95, (40, 20, 100, 90)),
            YoloDetection("cell phone", 0.91, (10, 10, 70, 110)),
        ]

        result = vision._run_yolo_security_gate(require_blink=True)

        self.assertFalse(result.ok)
        self.assertTrue(result.phone_detected)
        self.assertIn("Phone/screen", result.reason)

    def test_release_marks_camera_unavailable(self):
        vision = self.make_vision()
        camera = vision.camera

        vision.release()

        self.assertTrue(camera.released)
        self.assertIsNone(vision.camera)
        self.assertFalse(vision.camera_available)

    def test_face_encoding_serializes_without_pickle_for_new_data(self):
        vision = self.make_vision()
        encoding = np.arange(128, dtype=np.float64)

        encoded = vision._serialize_face_encoding(encoding)
        decoded = vision._deserialize_face_encoding(encoded)

        self.assertTrue(encoded.startswith(VisionAI.FACE_ENCODING_PREFIX))
        np.testing.assert_array_equal(decoded, encoding)

    def test_legacy_pickle_face_encoding_is_rejected_by_default(self):
        vision = self.make_vision()
        encoding = np.arange(128, dtype=np.float64)

        with self.assertRaises(ValueError):
            vision._deserialize_face_encoding(pickle.dumps(encoding))

    def test_legacy_pickle_face_encoding_can_be_enabled_for_migration(self):
        vision = self.make_vision()
        encoding = np.arange(128, dtype=np.float64)

        with patch("vision_ai.ALLOW_LEGACY_FACE_PICKLE", True):
            decoded = vision._deserialize_face_encoding(pickle.dumps(encoding))

        np.testing.assert_array_equal(decoded, encoding)

    def test_invalid_face_encoding_length_is_rejected(self):
        vision = self.make_vision()

        with self.assertRaises(ValueError):
            vision._deserialize_face_encoding(VisionAI.FACE_ENCODING_PREFIX + b"short")


if __name__ == "__main__":
    unittest.main()
