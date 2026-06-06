#!/usr/bin/env python3
"""
Generate a short synthetic video with simulated blink for testing.
"""
import cv2
import numpy as np
from pathlib import Path

def generate_test_video(output_path: str = "test_video.mp4", duration_sec: int = 4, fps: int = 15):
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_sec * fps

    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Draw a simple face
        cv2.rectangle(frame, (220, 140), (420, 380), (220, 200, 180), -1)  # face
        cv2.circle(frame, (280, 220), 25, (255, 255, 255), -1)            # left eye
        cv2.circle(frame, (360, 220), 25, (255, 255, 255), -1)            # right eye

        # Simulate blink (eye closed for a few frames)
        if 30 < i < 38 or 70 < i < 78:
            cv2.line(frame, (255, 220), (305, 220), (100, 80, 80), 8)     # left eye closed
            cv2.line(frame, (335, 220), (385, 220), (100, 80, 80), 8)     # right eye closed
        else:
            cv2.circle(frame, (280, 220), 8, (50, 50, 50), -1)            # left pupil
            cv2.circle(frame, (360, 220), 8, (50, 50, 50), -1)            # right pupil

        out.write(frame)

    out.release()
    print(f"[OK] Test video created: {output_path} ({duration_sec} sec, {fps} fps)")

if __name__ == "__main__":
    generate_test_video()
