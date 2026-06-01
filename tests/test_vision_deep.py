import pickle
import unittest
import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from vision_ai import VisionAI, YoloDetection


class FakeCamera:
    def __init__(self, frames):
        self._frames = list(frames)
        self.released = False

    def read(self):
        if not self._frames:
            return False, None
        return True, self._frames.pop(0)

    def release(self):
        self.released = True


class TestVisionDeep(unittest.TestCase):
    def make_vision(self):
        vision = VisionAI(mock=True)
        vision.mock = False
        vision.camera_available = True
        vision.camera = FakeCamera([np.zeros((64, 64, 3), dtype=np.uint8)])
        vision.yolo_enabled = True
        vision.yolo_model = object()
        vision.yolo_model_loaded = True
        vision.yolo_observation_seconds = 0.2
        vision.yolo_frame_interval_seconds = 0
        return vision

    def test_face_encoding_serialization_and_deserialization_errors(self):
        vision = self.make_vision()

        with self.assertRaisesRegex(ValueError, "128"):
            vision._serialize_face_encoding(np.zeros(64, dtype=np.float64))

        valid_encoding = np.ones(VisionAI.FACE_ENCODING_SIZE, dtype=np.float64)
        payload = vision._serialize_face_encoding(valid_encoding)
        decoded = vision._deserialize_face_encoding(payload)
        np.testing.assert_array_equal(decoded, valid_encoding)

        with self.assertRaises(ValueError):
            vision._deserialize_face_encoding(VisionAI.FACE_ENCODING_PREFIX + b"short")

        with self.assertRaisesRegex(ValueError, "Pickle is no longer supported"):
            vision._deserialize_face_encoding(pickle.dumps(valid_encoding))

    def test_yolo_gate_is_fail_closed_when_model_unavailable(self):
        vision = self.make_vision()
        vision._load_yolo_model = MagicMock(return_value=False)
        vision.yolo_model_error = "YOLO model unavailable."

        result = vision._run_yolo_security_gate(require_blink=False)

        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "YOLO model unavailable.")

    def test_yolo_gate_rejects_phone_or_screen_like_detections(self):
        vision = self.make_vision()
        vision._load_yolo_model = MagicMock(return_value=True)
        vision._analyze_frame_with_yolo = MagicMock(
            return_value=[
                YoloDetection("face", 0.9, (20, 20, 40, 40)),
                YoloDetection("screen", 0.95, (5, 5, 10, 10)),
            ]
        )

        result = vision._run_yolo_security_gate(require_blink=False)

        self.assertFalse(result.ok)
        self.assertTrue(result.phone_detected)
        self.assertIn("Phone/screen-like", result.reason)

    def test_blink_state_transitions(self):
        vision = self.make_vision()

        state, blink = vision._advance_blink_state("waiting_open", "open")
        self.assertEqual(state, "waiting_closed")
        self.assertFalse(blink)

        state, blink = vision._advance_blink_state(state, "open")
        self.assertEqual(state, "waiting_closed")
        self.assertFalse(blink)

        state, blink = vision._advance_blink_state(state, "closed")
        self.assertEqual(state, "waiting_reopen")
        self.assertFalse(blink)

        state, blink = vision._advance_blink_state(state, "closed")
        self.assertEqual(state, "waiting_reopen")
        self.assertFalse(blink)

        state, blink = vision._advance_blink_state(state, "open")
        self.assertEqual(state, "done")
        self.assertTrue(blink)

        done_state, done_blink = vision._advance_blink_state("done", "open")
        self.assertEqual(done_state, "done")
        self.assertTrue(done_blink)

    def test_crop_bounds_are_clamped(self):
        vision = self.make_vision()
        frame = np.zeros((48, 64, 3), dtype=np.uint8)

        crop = vision._crop_frame(frame, (-20, -10, 90, 60))

        self.assertIsNotNone(crop)
        self.assertEqual(crop.shape, (48, 64, 3))

    def test_verify_face_mock_mode_uses_stored_encoding(self):
        vision = VisionAI(mock=True)
        payload, _ = vision.capture_face_encoding()

        class MatchingDB:
            def get_face_encoding(self, _user_id):
                return payload

        self.assertTrue(vision.verify_face(1, MatchingDB()))

        vision.set_mock_face_identity("different-person")
        self.assertFalse(vision.verify_face(1, MatchingDB()))

    def test_verify_face_mock_mode_fails_without_stored_encoding(self):
        vision = VisionAI(mock=True)

        class MissingDB:
            def get_face_encoding(self, _user_id):
                return None

        self.assertFalse(vision.verify_face(1, MissingDB()))

    def test_verify_face_camera_unavailable_fails_closed(self):
        vision = VisionAI(mock=False)
        vision.camera = None
        vision.camera_available = False

        valid_encoding = VisionAI(mock=True)
        stored = valid_encoding._serialize_face_encoding(np.ones(128, dtype=np.float64))

        class StubDB:
            def get_face_encoding(self, _user_id):
                return stored

        vision.camera_available = False
        self.assertFalse(vision.verify_face(1, StubDB()))

    def test_detect_liveness_with_mocked_landmarks(self):
        vision = self.make_vision()
        vision.mock = False
        vision.camera_available = True

        fake_frame = np.zeros((8, 8, 3), dtype=np.uint8)
        fake_recognition = MagicMock()
        fake_recognition.face_landmarks.return_value = [
            {"left_eye": [(0, 0)] * 6, "right_eye": [(0, 0)] * 6},
        ]
        fake_cv2 = MagicMock()
        fake_cv2.COLOR_BGR2RGB = 42
        fake_cv2.cvtColor.return_value = fake_frame
        fake_cv2.getTickFrequency.return_value = 1000.0
        fake_cv2.getTickCount.side_effect = [0, 1000]

        with patch("vision_ai.face_recognition", fake_recognition), \
                patch("vision_ai.cv2", fake_cv2), \
                patch.object(vision, "_read_camera_frame", return_value=(True, fake_frame)), \
                patch.object(vision, "calculate_ear", return_value=0.1):
            self.assertTrue(vision.detect_liveness())

        fake_recognition.face_landmarks.assert_called_once_with(fake_frame)


if __name__ == "__main__":
    unittest.main()
