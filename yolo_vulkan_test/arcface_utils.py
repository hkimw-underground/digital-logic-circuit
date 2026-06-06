#!/usr/bin/env python3
"""
512-dimensional face embedding using InceptionResnetV1 (facenet-pytorch)
"""
from pathlib import Path
import torch
from facenet_pytorch import InceptionResnetV1
import cv2
import numpy as np

# Load model once
_device = torch.device('cpu')
_model = InceptionResnetV1(pretrained='vggface2').eval().to(_device)

def get_embedding(image_path: Path) -> np.ndarray:
    """Return 512-dim embedding"""
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(image_path)

    # Preprocess (resize + normalize)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (160, 160))
    img = (img / 255.0 - 0.5) / 0.5
    img = np.transpose(img, (2, 0, 1))
    tensor = torch.tensor(img).unsqueeze(0).float().to(_device)

    with torch.no_grad():
        embedding = _model(tensor)

    return embedding.cpu().numpy().flatten()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
