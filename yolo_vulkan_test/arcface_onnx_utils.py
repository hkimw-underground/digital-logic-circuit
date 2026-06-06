#!/usr/bin/env python3
"""
512-dimensional face embedding using ArcFace ONNX model + ONNX Runtime
"""
from pathlib import Path
import cv2
import numpy as np
import onnxruntime as ort

# ArcFace ONNX model expects 112x112 RGB images, normalized to [-1, 1]
INPUT_SIZE = 112


class ArcFaceONNX:
    def __init__(self, model_path: Path):
        self.session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def get_embedding(self, image_path: Path) -> np.ndarray:
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(image_path)

        # Preprocess (NHWC format for this model)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
        img = (img - 127.5) / 127.5
        img = img.astype(np.float32)
        img = np.expand_dims(img, axis=0)

        embedding = self.session.run([self.output_name], {self.input_name: img})[0]
        embedding = embedding.flatten()
        embedding = embedding / np.linalg.norm(embedding)  # L2 normalize
        return embedding


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
