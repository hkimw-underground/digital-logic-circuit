#!/usr/bin/env python3
"""Simple benchmark: 50 runs and report average + stddev"""
import time
import argparse
from pathlib import Path
import numpy as np
from infer_vulkan import get_vulkan_session, preprocess
import cv2


def benchmark(model_path: Path, image_path: Path, runs: int = 50, input_size: int = 640, threads: int = 4):
    session = get_vulkan_session(model_path, threads=threads)
    input_name = session.get_inputs()[0].name

    img = cv2.imread(str(image_path))
    blob, _, _, _ = preprocess(img, input_size)

    times = []
    for i in range(runs):
        t0 = time.perf_counter()
        session.run(None, {input_name: blob})
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)

    avg = np.mean(times)
    std = np.std(times)
    fps = 1000.0 / avg if avg > 0 else 0
    print(f"\n=== Benchmark ({runs} runs, imgsz={input_size}, threads={threads}) ===")
    print(f"Average: {avg:.1f} ms   |   FPS: {fps:.1f}")
    print(f"Stddev : {std:.1f} ms")
    print(f"Min    : {min(times):.1f} ms")
    print(f"Max    : {max(times):.1f} ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("models/yolov8s.onnx"))
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()

    benchmark(args.model, args.image, args.runs, args.imgsz, args.threads)
