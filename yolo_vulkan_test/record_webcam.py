#!/usr/bin/env python3
"""
Simple webcam recorder for liveness testing.
Records ~5 seconds of video.
"""
import cv2
import time
from pathlib import Path

def record_webcam(output_path: str = "my_face_test.mp4", duration_sec: int = 5, fps: int = 15):
    cap = cv2.VideoCapture(0)  # default webcam

    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check camera permission or device.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"[INFO] Recording for {duration_sec} seconds... (press Ctrl+C to stop early)")
    start = time.time()

    while time.time() - start < duration_sec:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        cv2.imshow("Recording (press q to stop)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    out.release()
    cap.release()
    cv2.destroyAllWindows()
    print(f"[OK] Video saved: {output_path}")

if __name__ == "__main__":
    record_webcam()
