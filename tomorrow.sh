#!/usr/bin/env bash
# Tomorrow live demo helper for the 2FA doorlock project.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "[FAIL] .venv is missing. Run ./setup.sh first."
  exit 1
fi

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-4}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-4}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-4}"

cmd="${1:-preflight}"
shift || true

case "$cmd" in
  preflight)
    .venv/bin/python tools/tomorrow_live_check.py "$@"
    ;;
  quick)
    .venv/bin/python tools/tomorrow_live_check.py --skip-face --skip-e2e "$@"
    ;;
  mockface)
    .venv/bin/python tools/tomorrow_live_check.py --mock-face-only "$@"
    ;;
  esp32cam)
    DOORLOCK_CAMERA_URL="${DOORLOCK_ESP32CAM_CAMERA_URL:-serial:auto}" \
      .venv/bin/python tools/tomorrow_live_check.py --skip-e2e "$@"
    ;;
  upload-esp32)
    port="${1:-${DOORLOCK_ESP32CAM_UPLOAD_PORT:-}}"
    if [ -z "$port" ]; then
      .venv/bin/python tools/list_serial_ports.py || true
      echo "[FAIL] ESP32-CAM upload port required. Example: ./tomorrow.sh upload-esp32 /dev/ttyUSB0"
      exit 2
    fi
    bin/arduino-cli upload -p "$port" --fqbn esp32:esp32:esp32cam esp32cam/serial_camera/serial_camera.ino
    ;;
  live)
    .venv/bin/python tools/tomorrow_live_check.py --hardware "$@"
    ;;
  actuate)
    .venv/bin/python tools/tomorrow_live_check.py --hardware --actuate "$@"
    ;;
  server)
    exec .venv/bin/python server/main.py
    ;;
  server-esp32)
    DOORLOCK_CAMERA_URL="${DOORLOCK_ESP32CAM_CAMERA_URL:-serial:auto}" \
      exec .venv/bin/python server/main.py
    ;;
  test)
    .venv/bin/python run_tests.py
    ;;
  *)
    echo "Usage: ./tomorrow.sh {preflight|quick|mockface|esp32cam|upload-esp32|live|actuate|server|server-esp32|test}"
    exit 2
    ;;
esac
