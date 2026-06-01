# 교수님 시연 가이드 (2025 캡스톤)

## 1. 가장 빠른 실행 (추천)

```bash
./demo.sh
```

- 자동으로 **VISION_MOCK=true**, **YOLO 비활성**, Serial 미연결 상태로 시작
- 브라우저에서 `http://localhost:8080` 접속
- `--clean` 옵션으로 깨끗한 DB부터 시작 가능: `./demo.sh --clean`

## 2. 실제 하드웨어로 첫 부팅 — 문제 없이 성공하는 법 (내일용)

### 사전 준비 (아두이노 연결 전)
1. `pin_connect_set.md` 최신 버전 따라 **순서대로** 배선 완료
2. 펌웨어 업로드 (Arduino IDE 또는 arduino-cli)
3. USB-C 케이블로 아두이노 연결 (가능하면 **충분한 전류** 나오는 포트나 허브 사용)

### 실행 명령 (추천)
```bash
source .venv/bin/activate
DOORLOCK_VISION_MOCK=false \
DOORLOCK_YOLO_ENABLED=false \
python server/main.py
```

**성공 신호 (콘솔에 이게 떠야 함)**
- `✅ [성공] Arduino 연결됨: /dev/ttyACM*` 또는 실제 자동 매칭된 `/dev/ttyUSB*`
- 아두이노에서 "SYSTEM_READY" 두 번 출력됨 (펌웨어가 첫 부팅 안정화를 위해 두 번 보냄)
- 웹 GUI의 Hardware Link Status에서 Arduino와 카메라 상태가 표시됨
- 그 후 키패드나 NFC 입력하면 바로 반응

### 첫 부팅 문제 해결 체크 (90%는 여기서 걸림)
- 전원 부족 → 서보 떨림 + 부저 소리 약함 → **외부 5V 어댑터 강추**
- 시리얼 포트 늦게 잡힘 → Python이 자동으로 5초마다 재시도함 (기다리면 됨)
- 레벨 시프터 배선 실수 → NFC가 전혀 반응 안 함 (가장 흔한 실수)

ESP32-CAM을 USB-C로 노트북에 직접 꽂는 경우에는 일반 웹캠처럼 `DOORLOCK_CAMERA_URL=0`으로 잡히지 않는다. 먼저 `esp32cam/serial_camera/serial_camera.ino`를 ESP32-CAM에 업로드한 뒤, 서버는 `DOORLOCK_CAMERA_URL=serial:auto` 또는 실제 포트(`serial:/dev/ttyUSB0`)로 실행한다.

## 3. 시연 추천 시나리오 (5~7분)

1. **등록 흐름** (`/register`)
   - 이름 + NFC UID (예: `DEMO1234`) + PIN (예: `12345678`) 입력
   - "Capture Face Encoding" 클릭 → 성공 메시지 확인
   - Register Identity

2. **정상 2FA 성공**
   - 메인 화면에서 등록한 NFC UID 또는 PIN 입력 (Arduino 또는 콘솔에서 `WAKEUP:NFC:DEMO1234` 직접 입력 가능)
   - 로그에 `FINAL_SUCCESS` + OPEN_DOOR 명령 확인

3. **실패 케이스**
   - 등록되지 않은 UID → `UNAUTHORIZED` + AUTH_FAIL + 스냅샷
   - 등록된 사용자지만 얼굴 인식 실패 (mock에서는 자동으로 실패 처리 가능) → `FINAL_FAIL`

4. **연속 실패 → Lockdown**
   - 잘못된 PIN 3회 이상 입력 → 자동 LOCKDOWN 명령 + 화면 상단 경고 배너

5. **수동 제어**
   - "Open Door", "Initiate Lockdown" 버튼으로 직접 명령 송신

6. **사용자 관리**
   - `/users_page`에서 등록자 삭제 → 삭제 후 로그에서 "Unknown"으로 표시되는 것 확인

## 4. 하드웨어 없이 SW 전체 테스트하기 (강력 추천)

실제 Arduino, NFC, 키패드, 서보 없이도 **백엔드 + 웹 UI + 인증 로직 전체**를 매우 현실적으로 테스트할 수 있다.

실제 Chrome GUI까지 포함해서 등록, 얼굴 mock 비교, 성공/실패 인증, 로그 렌더링, 수동 제어, 사용자 삭제를 한 번에 검증:

```bash
./verify_full_pipeline.sh
```

### 4.1 Fake Arduino Simulator 사용법

터미널 두 개를 준비한다.

**터미널 A (가짜 아두이노)**
```bash
python server/fake_arduino.py
```

출력 예시:
```
/dev/pts/3
```

**터미널 B (서버)**
```bash
DOORLOCK_VISION_MOCK=true \
DOORLOCK_YOLO_ENABLED=false \
DOORLOCK_SERIAL_PORT=/dev/pts/3 \
DOORLOCK_WEB_PORT=8080 \
python server/main.py
```

이제 터미널 A의 메뉴에서 숫자를 누르면 실제 시리얼 통신과 동일한 신호가 서버로 들어간다.

### 4.2 미리 검증할 수 있는 중요 상황들

| 상황 | Fake Arduino 명령 | 예상되는 서버 동작 |
|------|-------------------|---------------------|
| 정상 2FA 성공 | `1` (NFC) 또는 `2` (PIN) | `FINAL_SUCCESS` 로그 + `OPEN_DOOR` 명령 |
| 1차 인증 실패 | `3` 또는 `4` | `UNAUTHORIZED` + `AUTH_FAIL` + 스냅샷 촬영 |
| Rate Limit | `6` | 두 번째 입력 즉시 무시 + "[DENIED] Rate limited" |
| **Lockdown 진입** | `5` (12회 폭주) | 10회 초과 시 입력 차단 + `LOCKDOWN` 명령 + 웹 UI 빨간 배너 |
| 오염된 데이터 | `7` | 서버가 gracefully 무시하고 계속 동작 |
| 문 열림 → 자동 잠김 시뮬레이션 | `OPEN_DOOR` 받으면 자동으로 `DOOR_OPENED` / `DOOR_CLOSED` 피드백 | 펌웨어 로직과 동일한 타이밍 확인 가능 |

### 4.3 자동 재현 (스크립트로)

```bash
# LOCKDOWN 상황을 5초 만에 재현
python server/fake_arduino.py --scenario lockdown

# Rate limit 동작만 빠르게 확인
python server/fake_arduino.py --scenario rate_limit
```

이 도구로 내일 시연 전에 **모든 실패/성공/보안 로직**을 미리 돌려보고 확신을 가질 수 있다.

## 5. 주의사항

- YOLO 모델이 없어도 demo.sh로는 문제없이 동작
- face_recognition / dlib 설치가 불안정해도 MOCK 모드에서는 무시됨
- 실제 Arduino 연결 시 전원 부족 주의 (서보 + 부저 동시 동작 시 외부 5V 권장)

## 6. 내일 현장 점검 명령

패키지, 환경 변수, 펌웨어 컴파일만 빠르게 확인:

```bash
./tomorrow.sh quick
```

카메라 없이 mock face encoding으로 웹 등록, DB 저장, 시리얼 인증, `OPEN_DOOR`, 실패 처리, `LOCKDOWN` API까지 확인:

```bash
./tomorrow.sh mockface
```

실제 얼굴 인증까지 포함한 사전 점검:

```bash
./tomorrow.sh preflight
```

ESP32-CAM USB-C Serial 카메라 기준 사전 점검:

```bash
./tomorrow.sh esp32cam
```

Arduino를 연결한 뒤 키패드/NFC 입력까지 확인:

```bash
./tomorrow.sh live
```

서보/부저 명령까지 직접 보내는 최종 점검:

```bash
./tomorrow.sh actuate
```

실제 서버 실행:

```bash
./tomorrow.sh server
```

ESP32-CAM USB-C Serial 카메라로 실제 서버 실행:

```bash
./tomorrow.sh server-esp32
```

`preflight`에서 얼굴이 검출되지 않으면 마지막 카메라 프레임이 `captures/preflight_camera.jpg`에 저장된다. 얼굴이 화면 중앙에 보이도록 앉은 뒤 다시 실행한다.

AMD Ryzen 5 4500U 환경에서는 시연 핵심 경로를 CPU 기반 face_recognition으로 둔다. YOLO/Vulkan 가속은 별도 모델 변환과 런타임 검증이 필요해서 내일 시연 경로에서는 끄는 것이 안전하다.

---

모든 자동 테스트는 `python3 run_tests.py`로 실행한다.

시연 중 문제가 생기면 콘솔 로그를 가장 먼저 확인하세요.
