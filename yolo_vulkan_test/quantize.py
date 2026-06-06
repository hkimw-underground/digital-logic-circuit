#!/usr/bin/env python3
"""
Static INT8 quantization for YOLO ONNX model (Vulkan-friendly).
Requires onnxruntime and a small calibration dataset.
"""
from pathlib import Path
import onnxruntime as ort
from onnxruntime.quantization import quantize_static, QuantType, CalibrationDataReader
import numpy as np
import cv2
import glob


class SimpleCalibrationReader(CalibrationDataReader):
    def __init__(self, image_folder: str, input_size: int = 640, max_samples: int = 50):
        self.images = glob.glob(str(Path(image_folder) / "*.*"))[:max_samples]
        self.input_size = input_size
        self.idx = 0

    def get_next(self):
        if self.idx >= len(self.images):
            return None
        img = cv2.imread(self.images[self.idx])
        self.idx += 1
        if img is None:
            return self.get_next()

        h, w = img.shape[:2]
        scale = min(self.input_size / h, self.input_size / w)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(img, (new_w, new_h))

        canvas = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        top = (self.input_size - new_h) // 2
        left = (self.input_size - new_w) // 2
        canvas[top:top+new_h, left:left+new_w] = resized

        blob = canvas.astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))[None, ...]
        return {"images": blob}


def quantize_model(model_path: Path, output_path: Path, calib_folder: str, input_size: int = 640):
    print(f"[INFO] Quantizing {model_path} -> {output_path}")

    reader = SimpleCalibrationReader(calib_folder, input_size)
    quantize_static(
        str(model_path),
        str(output_path),
        calibration_data_reader=reader,
        weight_type=QuantType.QInt8,
        activation_type=QuantType.QInt8,
    )
    print(f"[SUCCESS] INT8 model saved: {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--calib", type=str, required=True, help="Folder with calibration images")
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    quantize_model(args.model, args.output, args.calib, args.imgsz)
