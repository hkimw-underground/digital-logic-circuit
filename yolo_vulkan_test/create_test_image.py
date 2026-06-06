#!/usr/bin/env python3
"""Create a simple test image for benchmarking"""
import cv2
import numpy as np
from pathlib import Path

def create_test_image(output_path: str = "test_image.jpg", size: tuple = (640, 480)):
    """Create a simple gradient test image"""
    img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    
    # Create a simple gradient + some shapes
    for y in range(size[1]):
        for x in range(size[0]):
            img[y, x] = [
                int(255 * (x / size[0])),
                int(255 * (y / size[1])),
                int(128 + 127 * np.sin(x / 50))
            ]
    
    # Add a white rectangle (simulates a face-like region)
    cv2.rectangle(img, (200, 150), (400, 350), (255, 255, 255), -1)
    cv2.circle(img, (280, 220), 30, (200, 200, 200), -1)
    cv2.circle(img, (320, 220), 30, (200, 200, 200), -1)
    
    cv2.imwrite(output_path, img)
    print(f"[OK] Test image created: {output_path} ({size[0]}x{size[1]})")

if __name__ == "__main__":
    create_test_image()
