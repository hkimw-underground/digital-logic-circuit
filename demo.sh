#!/usr/bin/env bash
# demo.sh — 교수님 시연용 원클릭 런처 (Mock 모드, 안전)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "  2FA 스마트 도어락 — 교수님 시연용 데모 모드"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# 1. 가상환경 확인
if [ ! -d ".venv" ]; then
    echo "[1/4] 가상환경이 없습니다. setup.sh를 먼저 실행하세요."
    echo "      ./setup.sh"
    exit 1
fi

source .venv/bin/activate

# 2. 데모에 최적화된 환경변수 강제 설정 (실제 하드웨어 없이도 동작)
export DOORLOCK_VISION_MOCK=true
export DOORLOCK_YOLO_ENABLED=false
export DOORLOCK_SERIAL_PORT=/dev/ttyUSB999   # 존재하지 않는 포트 → graceful fallback
export DOORLOCK_WEB_PORT=8080
export DOORLOCK_WEB_HOST=0.0.0.0

echo "[2/4] 데모 모드 환경 설정 완료"
echo "      - Vision: MOCK (실제 카메라/얼굴인식 불필요)"
echo "      - YOLO: 비활성"
echo "      - Serial: 연결되지 않은 상태로 시작 (명령은 콘솔에만 출력)"
echo ""

# 3. 오래된 DB sidecar 정리 (선택, 깨끗한 상태로 시작하고 싶을 때)
if [ "$1" = "--clean" ]; then
    echo "[3/4] 기존 DB 파일 정리 중..."
    rm -f server/doorlock.db* server/doorlock_backup.db* 2>/dev/null || true
    echo "      ✓ 깨끗한 DB로 시작"
else
    echo "[3/4] 기존 DB 유지 (사용자/로그 보존)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  서버 시작 중... (Ctrl+C 로 종료)"
echo "  브라우저에서 다음 주소 접속:"
echo "    http://localhost:8080"
echo "    http://<학교-PC-IP>:8080"
echo ""
echo "  시연 시나리오:"
echo "  1. /register 페이지에서 사용자 등록 (NFC UID + PIN + 얼굴 캡처)"
echo "  2. 메인 화면에서 로그 실시간 확인"
echo "  3. 등록된 NFC/PIN으로 인증 시도 → 얼굴 통과 → OPEN_DOOR 명령 확인"
echo "  4. 잘못된 인증 → AUTH_FAIL + 스냅샷 + Discord 알림(설정 시)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

python3 server/main.py
