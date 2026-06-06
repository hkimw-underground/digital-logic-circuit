#!/usr/bin/env python3
"""
512-dim ArcFace ONNX Embedding + MediaPipe Liveness Verification
"""
import argparse
import time
from pathlib import Path
import cv2
import numpy as np
from arcface_onnx_utils import ArcFaceONNX, cosine_similarity
from video_liveness import analyze_video

THRESHOLD = 0.60  # cosine similarity threshold for 512-dim ArcFace


def extract_face_crop(video_path: Path, yolo_model_path: Path) -> np.ndarray:
    """Extract the first detected face crop from the video."""
    from ultralytics import YOLO

    yolo = YOLO(str(yolo_model_path))
    cap = cv2.VideoCapture(str(video_path))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = yolo(frame, imgsz=384, verbose=False)
        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                # Take the first face box
                box = r.boxes[0].xyxy[0].cpu().numpy().astype(int)
                x1, y1, x2, y2 = box
                crop = frame[y1:y2, x1:x2]
                if crop.size > 0:
                    cap.release()
                    return crop

    cap.release()
    return None


def verify(video_path: Path, enrolled_embedding: np.ndarray, yolo_model: Path, arcface_model: Path):
    start = time.perf_counter()

    # 1. Liveness check (MediaPipe)
    liveness_result, elapsed_liveness = analyze_video(video_path, yolo_model, imgsz=384)
    if "Real" not in liveness_result:
        return "Spoof (liveness failed)", time.perf_counter() - start

    # 2. Extract face crop and run ArcFace ONNX
    face_crop = extract_face_crop(video_path, yolo_model)
    if face_crop is None:
        return "Spoof (no face detected)", time.perf_counter() - start

    if not arcface_model.exists():
        print("[ERROR] ArcFace ONNX model not found.")
        print("Run this first: python download_arcface_onnx.py")
        return "Error (ArcFace model missing)", time.perf_counter() - start

    extractor = ArcFaceONNX(arcface_model)

    # Save temp crop for ArcFace (expects file path)
    temp_path = Path("/tmp/face_crop_verify.jpg")
    cv2.imwrite(str(temp_path), face_crop)
    embedding = extractor.get_embedding(temp_path)

    sim = cosine_similarity(enrolled_embedding, embedding)
    result = "Real" if sim >= THRESHOLD else f"Spoof (sim={sim:.3f})"

    total_time = time.perf_counter() - start
    return result, total_time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--enrolled", type=Path, required=True, help="Path to .npy 512-dim embedding")
    parser.add_argument("--yolo-model", type=Path, default=Path("models/yolov8m.pt"))
    parser.add_argument("--arcface-model", type=Path, default=Path("models/arcface.onnx"))
    args = parser.parse_args()

    enrolled = np.load(args.enrolled)

    result, elapsed = verify(args.video, enrolled, args.yolo_model, args.arcface_model)
    print(f"\n=== Result ===")
    print(f"Decision : {result}")
    print(f"Time     : {elapsed:.2f} sec")


if __name__ == "__main__":
    main()
