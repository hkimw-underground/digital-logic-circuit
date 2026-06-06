#!/usr/bin/env python3
"""
YOLO inference using ONNX Runtime + Vulkan EP (forced).
Includes provider verification and timing.
"""
import argparse
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


def get_vulkan_session(model_path: Path, force_vulkan: bool = True, threads: int = 4):
    """Create ONNX Runtime session preferring / forcing Vulkan EP with tuned threads."""
    available_providers = ort.get_available_providers()
    print(f"[INFO] Available providers: {available_providers}")

    providers = []
    if force_vulkan and "VulkanExecutionProvider" in available_providers:
        providers.append("VulkanExecutionProvider")
        print("[INFO] Forcing VulkanExecutionProvider")
    elif "VulkanExecutionProvider" in available_providers:
        providers.append("VulkanExecutionProvider")
        print("[INFO] VulkanExecutionProvider available, using it")
    else:
        print("[WARN] VulkanExecutionProvider NOT available. Falling back to CPU.")

    providers.append("CPUExecutionProvider")

    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.intra_op_num_threads = threads
    sess_options.inter_op_num_threads = 1
    sess_options.enable_mem_pattern = True
    sess_options.enable_cpu_mem_arena = True

    session = ort.InferenceSession(
        str(model_path),
        sess_options=sess_options,
        providers=providers
    )

    active_providers = session.get_providers()
    print(f"[INFO] Active providers: {active_providers}")

    if "VulkanExecutionProvider" not in active_providers:
        print("[ERROR] VulkanExecutionProvider failed to initialize.")
    else:
        print("[SUCCESS] Running on Vulkan EP")

    return session


def preprocess(img: np.ndarray, input_size: int = 640):
    """Letterbox + normalize for YOLO (NumPy optimized)"""
    h, w = img.shape[:2]
    scale = min(input_size / h, input_size / w)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    pad_w = input_size - new_w
    pad_h = input_size - new_h
    top = pad_h // 2
    left = pad_w // 2

    canvas = np.full((input_size, input_size, 3), 114, dtype=np.uint8)
    canvas[top:top+new_h, left:left+new_w] = resized

    blob = canvas.astype(np.float32) / 255.0
    blob = np.transpose(blob, (2, 0, 1))[None, ...]
    return blob, scale, left, top


def run_inference(session, img_path: Path, input_size: int = 640):
    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(img_path)

    input_name = session.get_inputs()[0].name

    blob, scale, left, top = preprocess(img, input_size)

    t0 = time.perf_counter()
    outputs = session.run(None, {input_name: blob})
    t1 = time.perf_counter()

    print(f"[RESULT] Inference time: {(t1 - t0) * 1000:.1f} ms  |  imgsz={input_size}")
    print(f"[RESULT] Output shape: {outputs[0].shape}")

    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("models/yolov8s.onnx"))
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--force-vulkan", action="store_true", default=True)
    args = parser.parse_args()

    if not args.model.exists():
        print(f"[ERROR] Model not found: {args.model}")
        return

    session = get_vulkan_session(args.model, force_vulkan=args.force_vulkan, threads=args.threads)
    run_inference(session, args.image, input_size=args.imgsz)


if __name__ == "__main__":
    main()
