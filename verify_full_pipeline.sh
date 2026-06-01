#!/usr/bin/env bash
# Full local validation: browser GUI, software tests, Python stack, firmware compile.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "[FAIL] .venv is missing. Run ./setup.sh first."
  exit 1
fi

.venv/bin/python tools/gui_pipeline_check.py
.venv/bin/python run_tests.py
./tomorrow.sh quick
