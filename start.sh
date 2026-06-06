#!/bin/bash
# 2FA 스마트 도어락 서버 실행 스크립트 (ESP32-CAM 우선, 1ST_SUCCESS 피드백 포함)

set -e

cd "$(dirname "$0")"

echo "=== 2FA Doorlock Server ==="
echo "Activating venv..."
source .venv/bin/activate 2>/dev/null || true

echo "Starting with YOLO + Blink detection enabled (anti-spoofing)..."
echo "1ST_SUCCESS feedback enabled."
echo ""

DOORLOCK_VISION_MOCK=false \
DOORLOCK_YOLO_ENABLED=true \
DOORLOCK_FACE_LIVENESS_REQUIRED=true \
DOORLOCK_YOLO_REQUIRE_BLINK=true \
DOORLOCK_YOLO_CONFIDENCE=0.55 \
DOORLOCK_YOLO_FRAME_INTERVAL_SECONDS=0.25 \
DOORLOCK_CAMERA_URL=serial:auto \
DOORLOCK_ESP32CAM_BAUD_RATE=921600 \
exec python3 server/main.py
