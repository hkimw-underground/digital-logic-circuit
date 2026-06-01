#!/usr/bin/env bash
# setup.sh — 2FA 스마트 도어락 서버 환경 한 번에 세팅
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════"
echo "  2FA 스마트 도어락 — 환경 세팅"
echo "═══════════════════════════════════════════"

# 1. Python venv
if [ ! -d ".venv" ]; then
    echo "[1/5] Python 가상환경 생성..."
    python3 -m venv .venv
else
    echo "[1/5] 가상환경 이미 존재 → 건너뜀"
fi
source .venv/bin/activate

# 2. pip 업그레이드 + 의존성 설치
echo "[2/5] 의존성 설치..."
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>&1 | tail -5
echo "  ✓ 의존성 설치 완료"

# 3. models 디렉터리 준비
echo "[3/5] models 디렉터리 확인..."
mkdir -p models
if [ ! -f "models/doorlock_yolov8n.pt" ]; then
    echo "  ⚠  models/doorlock_yolov8n.pt 없음 (YOLO 비활성 상태로 실행 가능)"
fi

# 4. 시리얼 포트 탐색 (Arduino R4 WiFi = /dev/ttyACM*)
echo "[4/5] 시리얼 포트 탐색..."
FOUND_PORT=""
for p in /dev/ttyACM* /dev/ttyUSB*; do
    if [ -e "$p" ]; then
        echo "  → 감지됨: $p"
        FOUND_PORT="$p"
    fi
done
if [ -z "$FOUND_PORT" ]; then
    echo "  ⚠  Arduino가 연결되지 않았습니다. USB-C를 꽂은 뒤 다시 확인하세요."
else
    echo "  ✓ 시리얼 포트: $FOUND_PORT"
fi

# 5. Arduino cores
echo "[5/6] Arduino core 확인..."
if [ -x "bin/arduino-cli" ]; then
    if ! bin/arduino-cli core list | grep -q '^esp32:esp32'; then
        echo "  → ESP32 core 설치 (ESP32-CAM serial camera compile/upload용)"
        bin/arduino-cli core update-index --additional-urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
        bin/arduino-cli core install esp32:esp32 --additional-urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
    else
        echo "  ✓ ESP32 core 설치됨"
    fi
fi

# 6. .env 파일 생성 (없을 때만)
echo "[6/6] 환경 설정 파일 확인..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || true
    if [ -f ".env" ]; then
        if [ -n "$FOUND_PORT" ]; then
            sed -i "s|DOORLOCK_SERIAL_PORT=.*|DOORLOCK_SERIAL_PORT=$FOUND_PORT|" .env
        fi
        echo "  ✓ .env 파일 생성됨 (필요시 수정하세요)"
    fi
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  세팅 완료!"
echo ""
echo "  서버 실행:"
echo "    source .venv/bin/activate"
echo "    python3 server/main.py"
echo ""
if [ -z "$FOUND_PORT" ]; then
    echo "  ⚠ Arduino USB-C를 연결한 뒤 서버를 실행하세요."
fi
echo "═══════════════════════════════════════════"
