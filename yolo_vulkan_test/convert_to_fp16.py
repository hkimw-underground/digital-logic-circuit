#!/usr/bin/env python3
"""
Convert ONNX model (FP32) to FP16 for better performance on Vega iGPU.
Requires: onnx, onnxruntime, onnxconverter-common (or manual implementation)
"""
from pathlib import Path
import onnx
from onnxconverter_common import float16

def convert_fp16(input_path: Path, output_path: Path):
    print(f"[INFO] Converting {input_path} to FP16...")

    model = onnx.load(str(input_path))

    # Convert to FP16 (keep some nodes in FP32 if needed)
    model_fp16 = float16.convert_float_to_float16(
        model,
        keep_io_types=True,           # Keep input/output as FP32 for compatibility
        disable_shape_infer=True
    )

    onnx.save(model_fp16, str(output_path))
    print(f"[SUCCESS] FP16 model saved: {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    convert_fp16(args.input, args.output)
