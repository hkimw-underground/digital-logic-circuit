#!/usr/bin/env python3
"""Download YOLOv8 model (s or m)"""
from pathlib import Path
from ultralytics import YOLO
import argparse

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="yolov8m", choices=["yolov8s", "yolov8m"])
    args = parser.parse_args()

    target = MODEL_DIR / f"{args.model}.pt"
    if target.exists():
        print(f"[OK] {target} already exists.")
        return

    print(f"[INFO] Downloading {args.model}.pt ...")
    model = YOLO(f"{args.model}.pt")
    model.save(str(target))
    print(f"[DONE] Saved to {target}")

if __name__ == "__main__":
    main()
