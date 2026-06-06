#!/usr/bin/env python3
"""
Download a 512-dimensional ArcFace ONNX model for face embedding extraction.
"""
from pathlib import Path
import urllib.request
import sys

MODEL_NAME = "arcface.onnx"

# Primary + fallback sources (512-dim ArcFace ONNX)
URLS = [
    "https://huggingface.co/AdamCodd/arcface-resnet50/resolve/main/arcface-resnet50.onnx",
    "https://huggingface.co/sajjjad/arcface/resolve/main/arcface.onnx",
]


def download_model(output_dir: Path = Path("models")):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / MODEL_NAME

    if output_path.exists():
        print(f"[OK] Model already exists: {output_path}")
        return output_path

    for url in URLS:
        print(f"[INFO] Trying: {url}")
        try:
            urllib.request.urlretrieve(url, output_path)
            print(f"[OK] Downloaded to {output_path}")
            return output_path
        except Exception as e:
            print(f"[WARN] Failed: {e}")

    print("\n[ERROR] All download attempts failed.")
    print(f"Please manually download a 512-dim ArcFace ONNX model and place it at:")
    print(f"  {output_path}")
    print("Recommended (direct download):")
    print("  https://huggingface.co/AdamCodd/arcface-resnet50/resolve/main/arcface-resnet50.onnx")
    sys.exit(1)


if __name__ == "__main__":
    download_model()