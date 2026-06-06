#!/usr/bin/env python3
"""
Enroll a new user with 512-dimensional ArcFace ONNX embedding
"""
import argparse
from pathlib import Path
import numpy as np
from arcface_onnx_utils import ArcFaceONNX

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("models/arcface.onnx"))
    parser.add_argument("--output", type=Path, default=Path("enrolled.npy"))
    args = parser.parse_args()

    if not args.model.exists():
        print(f"[ERROR] ArcFace ONNX model not found: {args.model}")
        print("Run this first:")
        print("  python download_arcface_onnx.py")
        return

    extractor = ArcFaceONNX(args.model)
    embedding = extractor.get_embedding(args.image)
    np.save(args.output, embedding)
    print(f"[OK] 512-dim embedding saved to {args.output}")

if __name__ == "__main__":
    main()
