#!/usr/bin/env python3
"""
Record 10 short face videos for blink/liveness testing.
Each clip is ~5 seconds.
"""
import cv2
import time
from pathlib import Path

SAMPLES_DIR = Path("face_samples")
SAMPLES_DIR.mkdir(exist_ok=True)

TOTAL_SAMPLES = 10
DURATION_SEC = 5
FPS = 15
PAUSE_BETWEEN = 3


def record_one(output_path: Path, duration: int, fps: int):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Webcam not available.")
        return False

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    print(f"[REC] Recording {output_path.name} ... ({duration}s)")
    start = time.time()

    while time.time() - start < duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        cv2.imshow("Recording - Press 'q' to stop", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    out.release()
    cap.release()
    cv2.destroyAllWindows()
    print(f"[OK] Saved: {output_path}")
    return True


def main():
    print(f"=== Recording {TOTAL_SAMPLES} face samples ===")
    print("Please blink naturally during each recording.\n")

    for i in range(1, TOTAL_SAMPLES + 1):
        filename = f"face_sample_{i:02d}.mp4"
        output_path = SAMPLES_DIR / filename

        record_one(output_path, DURATION_SEC, FPS)

        if i < TOTAL_SAMPLES:
            print(f"Waiting {PAUSE_BETWEEN}s before next recording...\n")
            time.sleep(PAUSE_BETWEEN)

    print("\n=== All samples recorded ===")
    print(f"Location: {SAMPLES_DIR.resolve()}")


if __name__ == "__main__":
    main()
