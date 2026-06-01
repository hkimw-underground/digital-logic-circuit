# 테스트 시나리오

이 문서는 2FA 스마트 도어락 시스템을 하드웨어 없이도 반복 검증하고, 실제 Arduino 연결 후에도 같은 기준으로 점검하기 위한 테스트 플레이북이다.

## 0. 테스트 기준

| 구분 | 기준 |
|---|---|
| 서버 진입점 | `server/main.py` |
| 웹 UI | FastAPI, 기본 `http://0.0.0.0:8000` |
| 데모 포트 | `DOORLOCK_WEB_PORT=8080` |
| DB | SQLite, 기본 `server/doorlock.db` |
| Arduino 통신 | USB Serial, `9600` baud |
| 인증 성공 명령 | `OPEN_DOOR` |
| 인증 실패 명령 | `AUTH_FAIL` |
| 보안 잠금 명령 | `LOCKDOWN` |
| 성공 로그 | `1ST_AUTH_SUCCESS`, `FINAL_SUCCESS` |
| 실패 로그 | `UNAUTHORIZED`, `FINAL_FAIL` |

## 1. 테스트 레벨

| 레벨 | 목적 | 하드웨어 필요 | 대표 명령 |
|---|---|---|---|
| Level 0 | 정적/자동 테스트 | 없음 | `python3 run_tests.py` |
| Level 1 | 서버 로직 직접 호출 | 없음 | `DoorLockServer.handle_wakeup()` |
| Level 2 | 웹 UI + 가상 Serial 통합 | 없음 | `tools/gui_pipeline_check.py` |
| Level 3 | 실제 Arduino/배선 검증 | 필요 | `python3 server/main.py` |

## 2. 공통 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

테스트 DB를 따로 쓰면 기존 시연 데이터를 건드리지 않는다.

```bash
export DOORLOCK_DB_PATH=/tmp/doorlock_test.db
```

테스트 종료 후 정리:

```bash
rm -f /tmp/doorlock_test.db /tmp/doorlock_test.db-wal /tmp/doorlock_test.db-shm
```

## 3. Level 0: 자동 테스트

### SC-00: 전체 Python 테스트 실행

```bash
python3 run_tests.py
```

기대 결과:

- 모든 `tests/test*.py`가 실행된다.
- 인증 성공/실패, DB 백업, 로그 마스킹, YOLO 게이트, 웹 API payload가 통과한다.

대체 명령:

```bash
python3 -B -m unittest discover -s tests -t . -p 'test*.py'
```

### SC-00B: 웹 문서 빌드 확인

사전 확인:

```bash
node --version
npm --version
```

`node` 또는 `npm`이 없으면 이 환경에서는 Docusaurus 빌드를 실행할 수 없다. Node.js 20 이상이 설치된 환경에서 아래 명령을 실행한다.

```bash
npm --prefix website run build
```

기대 결과:

- Docusaurus 문서가 빌드된다.
- Markdown/MDX 문법 오류가 없어야 한다.

### SC-00C: 실제 브라우저 GUI 전체 파이프라인

```bash
./verify_full_pipeline.sh
```

기대 결과:

- Chrome에서 `/register`를 열고 mock face encoding을 캡처한다.
- GUI 폼으로 사용자 등록 후 `/users_page`에서 사용자가 보인다.
- 등록된 NFC + 다른 mock face는 `AUTH_FAIL`이 된다.
- 등록된 NFC + 같은 mock face는 `OPEN_DOOR`가 된다.
- 잘못된 PIN은 `AUTH_FAIL`이 된다.
- 대시보드 로그에 `FINAL_SUCCESS`, `FINAL_FAIL`, `UNAUTHORIZED`가 렌더링된다.
- 대시보드 수동 `Open Door`, `Initiate Lockdown` 버튼이 각각 `OPEN_DOOR`, `LOCKDOWN`을 보낸다.
- GUI 삭제 후 사용자 목록은 비고, 기존 로그는 `Unknown`으로 남는다.

### SC-00D: ESP32-CAM USB-C Serial 카메라 점검

ESP32-CAM + CH340 보드는 일반 USB 웹캠이 아니므로 먼저 `esp32cam/serial_camera/serial_camera.ino`를 ESP32-CAM에 업로드해야 한다.

```bash
.venv/bin/python tools/list_serial_ports.py
./tomorrow.sh esp32cam
```

기대 결과:

- ESP32-CAM 포트가 `/dev/ttyUSB*` 또는 `/dev/serial/by-id/*`로 보인다.
- `DOORLOCK_CAMERA_URL=serial:auto` 기준으로 ESP32-CAM serial JPEG 프레임을 읽는다.
- 얼굴이 보이면 face encoding 캡처가 성공한다.

## 4. Level 1: 서버 로직 직접 검증

하드웨어 없이 `DoorLockServer`에 직접 시리얼 메시지를 주입한다. 가장 빠르고 재현성이 높다.

### 공통 스크립트

아래 명령은 임시 DB와 mock vision으로 서버 로직을 실행한다.

```bash
PYTHONPATH=server DOORLOCK_VISION_MOCK=true DOORLOCK_YOLO_ENABLED=false python3 - <<'PY'
import os
from unittest.mock import MagicMock, patch

from database import Database
from main import DoorLockServer
from vision_ai import VisionAI

db_path = "/tmp/doorlock_level1.db"
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(db_path + suffix)
    except FileNotFoundError:
        pass

db = Database(db_path=db_path)
db.add_user("DemoUser", nfc_uid="A1B2C3D4", password="12345678")

with patch("serial.Serial"):
    server = DoorLockServer(db=db, vision=VisionAI(mock=True))
server.ser = MagicMock()

def run(name, message):
    print(f"\n[{name}] {message}")
    server.last_failed_attempt = 0
    server.handle_wakeup(message)
    logs = db.get_recent_logs(limit=3)
    for log in logs:
        print(log)
    print("last command:", server.ser.write.call_args)

run("NFC success", "WAKEUP:NFC:A1B2C3D4")
run("PIN success", "WAKEUP:PW:12345678")
run("Unknown NFC", "WAKEUP:NFC:DEADBEEF")

server.shutdown()
PY
```

### SC-01: NFC 정상 인증

입력:

```text
WAKEUP:NFC:A1B2C3D4
```

기대 결과:

| 항목 | 기대값 |
|---|---|
| 1차 인증 | `Database.verify_nfc()` 성공 |
| 2차 인증 | mock vision에서 성공 |
| DB 로그 | `1ST_AUTH_SUCCESS` 후 `FINAL_SUCCESS` |
| Arduino 명령 | `OPEN_DOOR` |

### SC-02: PIN 정상 인증

입력:

```text
WAKEUP:PW:12345678
```

기대 결과:

| 항목 | 기대값 |
|---|---|
| 1차 인증 | bcrypt PIN 검증 성공 |
| DB 로그 method | `PASSWORD` |
| 최종 로그 | `FINAL_SUCCESS` |
| Arduino 명령 | `OPEN_DOOR` |

### SC-03: 등록되지 않은 NFC

입력:

```text
WAKEUP:NFC:DEADBEEF
```

기대 결과:

| 항목 | 기대값 |
|---|---|
| 1차 인증 | 실패 |
| 얼굴 인증 호출 | 호출하지 않음 |
| DB 로그 | `UNAUTHORIZED` |
| Arduino 명령 | `AUTH_FAIL` |
| 알림 메시지 | NFC UID 전체가 아니라 끝 4자리만 표시 |

### SC-04: 잘못된 PIN

입력:

```text
WAKEUP:PW:00000000
```

기대 결과:

| 항목 | 기대값 |
|---|---|
| DB 로그 | `UNAUTHORIZED` |
| Arduino 명령 | `AUTH_FAIL` |
| 콘솔/알림 | 실제 PIN 대신 `[REDACTED]` 표시 |

### SC-05: 2차 얼굴 인증 실패

재현:

```bash
PYTHONPATH=server DOORLOCK_VISION_MOCK=true DOORLOCK_YOLO_ENABLED=false python3 - <<'PY'
import os
from unittest.mock import MagicMock, patch
from database import Database
from main import DoorLockServer
from vision_ai import VisionAI

db_path = "/tmp/doorlock_face_fail.db"
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(db_path + suffix)
    except FileNotFoundError:
        pass

db = Database(db_path=db_path)
db.add_user("FaceFail", nfc_uid="FACE9999", password="1234")

with patch("serial.Serial"):
    server = DoorLockServer(db=db, vision=VisionAI(mock=True))
server.ser = MagicMock()
with patch.object(server.vision, "verify_face", return_value=False):
    server.handle_wakeup("WAKEUP:NFC:FACE9999")

print(db.get_recent_logs(limit=5))
print(server.ser.write.call_args)
server.shutdown()
PY
```

기대 결과:

- `1ST_AUTH_SUCCESS`가 먼저 기록된다.
- 얼굴 실패 후 `FINAL_FAIL`이 기록된다.
- Arduino에는 `AUTH_FAIL`이 전송된다.

### SC-06: malformed Serial 메시지 무시

입력 예시:

```text
WAKEUP:PW:
WAKEUP:FACE:1234
HELLO
```

기대 결과:

- DB 로그가 추가되지 않는다.
- Arduino 명령이 전송되지 않는다.
- 서버 프로세스가 계속 실행된다.

## 5. Level 2: Fake Arduino 통합 테스트

가상 PTY 시리얼 장치를 만들어 실제 `serial.Serial` 경로처럼 서버에 연결한다.

### 실행 방법

터미널 A:

```bash
python3 server/fake_arduino.py
```

출력되는 포트 예시:

```text
DOORLOCK_SERIAL_PORT=/dev/pts/3
```

터미널 B:

```bash
source .venv/bin/activate
DOORLOCK_VISION_MOCK=true \
DOORLOCK_YOLO_ENABLED=false \
DOORLOCK_SERIAL_PORT=/dev/pts/3 \
DOORLOCK_WEB_PORT=8080 \
python3 server/main.py
```

브라우저:

```text
http://localhost:8080
```

### SC-07: Fake Arduino 정상 연결

재현:

1. Fake Arduino에서 `8` 입력
2. 서버 콘솔 확인

기대 결과:

- Fake Arduino가 `SYSTEM_READY`를 보낸다.
- 서버 콘솔에 Arduino 부팅 완료 메시지가 표시된다.

### SC-08: 전체 스택 성공 경로

성공 경로는 등록된 UID를 정해 놓고 가상 Arduino가 그 UID를 보내게 만든다. 아래 방식은 PTY 포트를 먼저 출력하고, 서버를 연결한 뒤 Enter를 눌러 메시지를 보내므로 재현 순서가 명확하다.

터미널 B 실행 전:

```bash
PYTHONPATH=server DOORLOCK_DB_PATH=/tmp/doorlock_full_success.db python3 - <<'PY'
from database import Database
db = Database(db_path="/tmp/doorlock_full_success.db")
db.add_user("FakeSuccess", nfc_uid="A1B2C3D4", password="12345678")
db.close()
PY
```

터미널 A:

```bash
PYTHONPATH=server python3 - <<'PY'
import time
from fake_arduino import FakeArduino

fake = FakeArduino()
print(f"DOORLOCK_SERIAL_PORT={fake.slave_name}", flush=True)
input("Start the server with this port, then press Enter to send NFC success...")
fake.send("WAKEUP:NFC:A1B2C3D4")
time.sleep(5)
fake.running = False
PY
```

터미널 B:

```bash
DOORLOCK_DB_PATH=/tmp/doorlock_full_success.db \
DOORLOCK_VISION_MOCK=true \
DOORLOCK_YOLO_ENABLED=false \
DOORLOCK_SERIAL_PORT=/dev/pts/XX \
DOORLOCK_WEB_PORT=8080 \
python3 server/main.py
```

`/dev/pts/XX`는 터미널 A가 출력한 실제 포트로 바꾼다.

기대 결과:

- 서버 로그: 1차 인증 성공 후 mock face 인증 성공
- DB: `1ST_AUTH_SUCCESS`, `FINAL_SUCCESS`
- Fake Arduino 수신: `OPEN_DOOR`
- Fake Arduino 피드백: `DOOR_OPENED`, 약 3초 후 `DOOR_CLOSED`

### SC-09: Rate limit

SC-07 방식으로 Fake Arduino와 서버를 먼저 연결한 뒤, Fake Arduino 메뉴에서 `6`을 입력한다.

메뉴 `6`은 `WAKEUP:NFC:RATETEST1`을 보낸 뒤 0.3초 후 `WAKEUP:NFC:RATETEST2`를 보낸다.

기대 결과:

- 첫 번째 실패는 `UNAUTHORIZED`로 기록된다.
- 두 번째 입력은 3초 이내 재시도라 서버가 무시한다.
- 서버 콘솔에 `Rate limited` 메시지가 표시된다.

### SC-10: Lockdown

주의: 기본 설정에서는 rate limit이 3초라 Fake Arduino 메뉴 `5`의 빠른 연속 입력 대부분이 무시된다. 빠르게 Lockdown을 재현하려면 서버를 아래처럼 실행한다.

터미널 B:

```bash
DOORLOCK_VISION_MOCK=true \
DOORLOCK_YOLO_ENABLED=false \
DOORLOCK_RATE_LIMIT_SECONDS=0 \
DOORLOCK_LOCKDOWN_DELAY_SECONDS=0 \
DOORLOCK_SERIAL_PORT=/dev/pts/3 \
DOORLOCK_WEB_PORT=8080 \
python3 server/main.py
```

터미널 A에서는 `python3 server/fake_arduino.py`를 실행한 뒤 출력된 포트를 터미널 B의 `DOORLOCK_SERIAL_PORT`에 넣고, Fake Arduino 메뉴에서 `5`를 입력한다.

기대 결과:

| 단계 | 기대값 |
|---|---|
| 1-10번째 실패 | `UNAUTHORIZED` 로그가 누적됨 |
| 11번째 이후 입력 | 처리 전에 실패 수가 임계값 이상이라 `LOCKDOWN` 전송 |
| 웹 UI | 연속 실패 alert 표시 |
| 알림 | webhook 설정 시 보안 알림 전송 |

현재 서버 로직은 "10번째 실패를 처리하면서 바로 Lockdown"이 아니라, 최근 1시간 실패 수가 이미 10개 이상일 때 다음 입력부터 Lockdown으로 막는다.

### SC-11: 수동 제어 버튼

재현:

1. 웹 UI 접속
2. `Open Door` 클릭
3. `Initiate Lockdown` 클릭

기대 결과:

- Fake Arduino 창에서 `OPEN_DOOR`와 `LOCKDOWN`을 수신한다.
- 실제 하드웨어에서는 서보/부저가 각각 동작해야 한다.

### SC-12: 로그와 스냅샷 API

재현:

```bash
curl http://localhost:8080/api/logs
```

기대 결과:

- `logs` 배열이 반환된다.
- 최근 3개 terminal 실패가 연속이면 `alert: true`가 반환된다.
- 스냅샷이 있는 로그는 `/api/logs/{log_id}/snapshot`에서 JPEG로 받을 수 있다.

## 6. Level 3: 실제 하드웨어 테스트

`pin_connect_set.md` 배선을 끝낸 뒤 실행한다.

```bash
source .venv/bin/activate
DOORLOCK_VISION_MOCK=false \
DOORLOCK_YOLO_ENABLED=false \
python3 server/main.py
```

### SC-13: Arduino 부팅

기대 결과:

- 서버가 `/dev/ttyACM*`, `/dev/ttyUSB*` 후보 중 Arduino `PING` 응답이 있는 포트에 자동 연결된다.
- 웹 GUI의 Hardware Link Status에 Arduino 연결 상태가 표시된다.
- 콘솔에 `SYSTEM_READY` 수신 로그가 보인다.
- 부저에서 시스템 준비음이 난다.

### SC-14: TTP229 PIN 입력

재현:

1. TTP229에서 숫자 4개 이상 입력
2. Arduino Serial 또는 서버 콘솔 확인

기대 결과:

```text
[KEY] 1
[KEY] Length: 1
WAKEUP:PW:1234
```

서버에 등록된 PIN이면 얼굴 인증으로 넘어가고, 등록되지 않은 PIN이면 `AUTH_FAIL`이 내려간다.

### SC-15: MFRC522 NFC 입력

재현:

1. 등록된 NFC 태그를 MFRC522에 가까이 댄다.
2. 서버 콘솔과 웹 로그를 확인한다.

기대 결과:

```text
WAKEUP:NFC:<UID>
```

등록된 UID이면 `1ST_AUTH_SUCCESS` 이후 얼굴 인증이 실행된다. 등록되지 않은 UID이면 `UNAUTHORIZED`와 `AUTH_FAIL`이 기록된다.

### SC-16: 서보 열림/자동 잠김

재현:

1. 정상 인증을 완료하거나 웹 UI에서 `Open Door` 클릭
2. 서보 위치 확인

기대 결과:

- `OPEN_DOOR` 수신
- 서보가 `SERVO_UNLOCKED_POS=90`으로 이동
- `DOOR_OPENED` 출력
- 약 3초 뒤 `SERVO_LOCKED_POS=0`으로 복귀
- `DOOR_CLOSED` 출력

### SC-17: 카메라 장애 fail-closed

재현:

1. `DOORLOCK_VISION_MOCK=false`
2. 카메라를 연결하지 않거나 다른 앱에서 점유한다.
3. 등록된 NFC/PIN으로 인증 시도

기대 결과:

- 1차 인증은 성공할 수 있다.
- 얼굴 인증은 실패한다.
- `FINAL_FAIL`이 기록된다.
- `OPEN_DOOR`는 전송되지 않는다.

## 7. 관리자 기능 테스트

### SC-18: 사용자 등록

재현:

1. `/register` 접속
2. 이름, NFC UID, PIN 입력
3. 카메라 사용 가능 시 `Capture Face Encoding`
4. `Register Identity`

기대 결과:

- 이름은 80자 이하, control character 없음
- NFC UID는 4-32자리 HEX
- PIN은 4-8자리 숫자
- PIN은 bcrypt hash로 저장됨
- 등록 성공 후 `/api/users`에서 조회 가능

### SC-19: 사용자 삭제 후 로그 보존

재현:

1. `/users_page` 접속
2. 사용자 삭제
3. `/api/logs` 확인

기대 결과:

- `users` 레코드는 삭제된다.
- 기존 `access_logs.user_id`는 `NULL`로 바뀐다.
- UI에는 과거 로그 사용자가 `Unknown`으로 표시된다.

### SC-20: DB 백업

재현:

```bash
PYTHONPATH=server python3 - <<'PY'
from database import Database
db = Database(db_path="/tmp/doorlock_backup_src.db")
db.add_user("BackupUser", nfc_uid="BEEF1234", password="1234")
print(db.backup_to("/tmp/doorlock_backup_copy.db"))
db.close()
PY
```

기대 결과:

- 백업 SQLite 파일이 생성된다.
- 파일 권한은 `0600`이다.
- 원본 DB와 백업 DB의 users/logs 데이터가 일치한다.

## 8. 시연 전 권장 순서

1. `./tomorrow.sh quick`
2. `./tomorrow.sh mockface`
3. ESP32-CAM에 `esp32cam/serial_camera/serial_camera.ino` 업로드
4. ESP32-CAM USB-C 연결 후 `./tomorrow.sh esp32cam`
5. 실제 배선 연결
6. `./tomorrow.sh live`
7. `./tomorrow.sh actuate`
8. `./tomorrow.sh server-esp32`
9. 웹 UI에서 사용자 등록, 정상 성공, 실패, 수동 열림, Lockdown 확인
10. 웹 UI의 Hardware Link Status에서 Arduino/ESP32-CAM 연결 상태와 Retry 버튼 동작 확인

`mockface`는 실제 카메라 없이 deterministic face encoding을 등록하고, 웹 API + SQLite + DoorLockServer + PTY serial 경로로 `OPEN_DOOR`, `AUTH_FAIL`, `LOCKDOWN`까지 확인한다.

`preflight`는 실제 카메라 얼굴 검출이 필요하다. 얼굴 검출에 실패하면 `captures/preflight_camera.jpg`를 확인한 뒤 조명과 카메라 위치를 조정한다.

## 9. 코드 기준 검증 매트릭스

| 파일 | 검증 포인트 |
|---|---|
| `server/main.py` | `WAKEUP` 파싱, rate limit, lockdown, `OPEN_DOOR/AUTH_FAIL/LOCKDOWN` 전송 |
| `server/database.py` | bcrypt PIN, NFC 조회, 로그, 실패 카운트, 백업, 삭제 시 로그 보존 |
| `server/vision_ai.py` | mock mode, 카메라 fail-closed, YOLO phone/screen 차단, blink gate, face encoding 직렬화 |
| `server/web_app.py` | `/api/register`, `/api/logs`, `/api/control/open`, `/api/control/lockdown` |
| `server/fake_arduino.py` | PTY 기반 Serial 시뮬레이션, 대화형 rate limit/lockdown/garbage 시나리오 |
| `arduino/doorlock_firmware/doorlock_firmware.ino` | TTP229 8키 폴링, MFRC522 SPI, 서보 0/90도, 부저 패턴 |
| `arduino/ttp229_test/ttp229_test.ino` | 키패드 단독 진단 |

## 10. 알려진 주의점

| 주의점 | 영향 | 대응 |
|---|---|---|
| Fake Arduino 메뉴 `5`는 입력 간격이 빠름 | 기본 rate limit 때문에 실패 로그가 충분히 쌓이지 않음 | 서버 실행 시 `DOORLOCK_RATE_LIMIT_SECONDS=0` |
| `fake_arduino.py --scenario ...` 모드는 포트를 출력받아 서버에 연결하기 어렵다 | 서버 연결 전 메시지가 먼저 나갈 수 있음 | 대화형 메뉴 또는 SC-08의 custom sender 사용 |
| 루트 `arduino/doorlock.ino`는 레거시 | 현재 배선과 다름 | 현재 기준은 `arduino/doorlock_firmware/doorlock_firmware.ino` |
| 실제 YOLO 모델 파일이 없을 수 있음 | YOLO gate 사용 시 모델 로드 실패 | 데모는 `DOORLOCK_YOLO_ENABLED=false`, 모델 검증은 별도 진행 |
