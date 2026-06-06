#!/usr/bin/env python3
"""
Export YOLOv8s.pt to ONNX optimized for Vulkan EP.
- opset 17
- dynamic batch + dynamic image size
- simplify (if onnxsim available)
"""
from pathlib import Path
from ultralytics import YOLO

MODEL_PT = Path("models/yolov8s.pt")
MODEL_ONNX = Path("models/yolov8s.onnx")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=MODEL_PT)
    parser.add_argument("--output", type=Path, default=MODEL_ONNX)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    if not args.model.exists():
        print(f"[ERROR] {args.model} not found.")
        return

    print(f"[INFO] Loading {args.model} ...")
    model = YOLO(str(args.model))

    print(f"[INFO] Exporting to ONNX @ {args.imgsz}px ...")
    model.export(
        format="onnx",
        imgsz=args.imgsz,
        dynamic=True,
        opset=17,
        simplify=True,
        name=str(args.output),
    )

    if args.output.exists():
        print(f"[SUCCESS] ONNX model saved: {args.output}")
    else:
        print("[WARN] Export may have failed.")

if __name__ == "__main__":
    main()
