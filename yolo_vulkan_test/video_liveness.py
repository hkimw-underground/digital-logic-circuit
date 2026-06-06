#!/usr/bin/env python3
"""
Final Liveness Detection Script (Video + MediaPipe EAR Blink Detection)
- Model: YOLOv8m
- Resolution: 384px
- Max processing time: ~4 seconds
- Uses MediaPipe Face Mesh for reliable Eye Aspect Ratio (EAR) blink detection
"""
import argparse
import time
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp

MAX_TIME = 4.0

# MediaPipe Face Mesh eye landmark indices (simplified 6-point EAR)
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [263, 387, 385, 362, 380, 373]


def eye_aspect_ratio(landmarks, indices, image_width, image_height):
    """Compute EAR from MediaPipe landmarks"""
    points = []
    for i in indices:
        x = int(landmarks[i].x * image_width)
        y = int(landmarks[i].y * image_height)
        points.append((x, y))

    A = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
    B = np.linalg.norm(np.array(points[2]) - np.array(points[4]))
    C = np.linalg.norm(np.array(points[0]) - np.array(points[3]))
    return (A + B) / (2.0 * C)


def detect_blink_with_mediapipe(landmarks_list, threshold=0.22, min_blinks=1):
    """Detect blink using MediaPipe EAR"""
    if len(landmarks_list) < 6:
        return False

    blink_count = 0
    was_below = False
    w, h = 384, 384  # approximate, will be overridden

    for lm, ww, hh in landmarks_list:
        left_ear = eye_aspect_ratio(lm, LEFT_EYE_INDICES, ww, hh)
        right_ear = eye_aspect_ratio(lm, RIGHT_EYE_INDICES, ww, hh)
        avg_ear = (left_ear + right_ear) / 2.0

        if avg_ear < threshold:
            was_below = True
        elif was_below and avg_ear > threshold + 0.04:
            blink_count += 1
            was_below = False

    return blink_count >= min_blinks


def analyze_video(video_path: Path, model_path: Path, imgsz: int = 384):
    yolo_model = YOLO(str(model_path))
    mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        return "Error", 0.0

    landmarks_list = []
    start_time = time.perf_counter()
    frame_count = 0
    sample_interval = 3

    while True:
        if time.perf_counter() - start_time > MAX_TIME:
            break

        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % sample_interval != 0:
            continue

        h, w = frame.shape[:2]

        # YOLO face detection (fast pre-filter)
        results = yolo_model(frame, imgsz=imgsz, verbose=False)
        face_boxes = []
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == 0:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    face_boxes.append((x1, y1, x2, y2))

        if not face_boxes:
            continue

        # MediaPipe on detected face region
        for (x1, y1, x2, y2) in face_boxes:
            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size == 0:
                continue

            rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
            mesh_results = mp_face_mesh.process(rgb_crop)

            if mesh_results.multi_face_landmarks:
                for face_landmarks in mesh_results.multi_face_landmarks:
                    landmarks_list.append((face_landmarks.landmark, face_crop.shape[1], face_crop.shape[0]))

    cap.release()
    mp_face_mesh.close()
    elapsed = time.perf_counter() - start_time

    has_blink = detect_blink_with_mediapipe(landmarks_list)
    result = "Real" if has_blink else "Spoof (no blink detected)"

    return result, elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("models/yolov8m.pt"))
    parser.add_argument("--imgsz", type=int, default=384)
    args = parser.parse_args()

    if not args.video.exists():
        print(f"[ERROR] Video not found: {args.video}")
        return

    if not args.model.exists():
        print(f"[ERROR] Model not found: {args.model}")
        return

    print(f"[INFO] Analyzing video: {args.video}")
    result, elapsed = analyze_video(args.video, args.model, args.imgsz)

    print(f"\n=== Result ===")
    print(f"Decision : {result}")
    print(f"Time     : {elapsed:.2f} sec")


if __name__ == "__main__":
    main()
