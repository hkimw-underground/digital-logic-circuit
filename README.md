# 2FA 스마트 도어락

SYU - Sahmyook University
디지털 논리 회로 실습: 캡스톤디자인 브레드보드팀

NFC 또는 PIN으로 사용자를 먼저 확인하고, 카메라로 얼굴을 한 번 더 확인하는 스마트 도어락이다. Arduino는 입력과 릴레이를 맡고, Python 서버는 인증 흐름, 로그, 웹 화면, 얼굴 확인을 처리한다.

```text
출입 허용 = (정상 NFC 또는 정상 PIN) AND (YOLO 검사 통과 AND 등록 얼굴 일치)
```

실제 사용 모드는 안전을 우선한다. YOLO 모델, 카메라, 등록된 얼굴 정보, 필요한 라이브러리 중 하나라도 없으면 문을 열지 않는다.

## 시스템 구성

| 영역 | 파일 | 역할 |
| --- | --- | --- |
| 펌웨어 | `arduino/doorlock.ino` | NFC, 키패드, 릴레이 제어 |
| 서버 | `server/main.py` | 시리얼 수신, 2FA 흐름 제어, 실패 제한 |
| 데이터베이스 | `server/database.py` | SQLite, bcrypt PIN 해싱, 접근 로그 |
| 영상 확인 | `server/vision_ai.py` | YOLO 검사, 얼굴 자르기, 얼굴 대조 |
| 웹 화면 | `server/web_app.py` | 사용자 등록, 실시간 영상, 로그, 사진 |

얼굴 확인 흐름:

```text
카메라 화면 -> YOLO nano -> 얼굴 자르기 + 휴대폰/화면 차단 + 눈깜빡임 확인 -> face_recognition
```

YOLO는 원본 화면에서 얼굴, 휴대폰이나 화면, 눈 상태를 먼저 찾는다. 인증할 때는 눈을 뜬 상태에서 감았다가 다시 뜨는 동작이 필요하다. 그 다음 얼굴 부분만 잘라 등록된 얼굴 정보와 비교한다.

## 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 server/main.py
```

대시보드:
- 기본: `http://localhost:8000`
- `server/cert.pem`, `server/key.pem`이 있으면 `https://localhost:8000`

대시보드 bind 주소와 포트는 필요하면 아래처럼 조정한다.

```bash
export DOORLOCK_WEB_HOST=127.0.0.1
export DOORLOCK_WEB_PORT=8000
```

## 하드웨어

1. Arduino IDE에서 `MFRC522`, `Keypad` 라이브러리를 설치한다.
2. [하드웨어 사양](docs/hardware_spec.md)의 핀맵대로 배선한다.
3. `arduino/doorlock.ino`를 업로드한다.
4. 서버의 `DOORLOCK_SERIAL_PORT`를 실제 포트로 설정한다.

```bash
export DOORLOCK_SERIAL_PORT=/dev/ttyACM0
export DOORLOCK_BAUD_RATE=9600
python3 server/main.py
```

Arduino R4 Minima는 UNO 계열 핀 배치에 맞춰 사용할 수 있다. 업로드 전 Arduino IDE에서 보드와 포트를 R4 Minima로 선택한다.

## 영상 모델

기본 모델 경로:

```bash
export DOORLOCK_YOLO_MODEL_PATH=models/doorlock_yolov8n.pt
```

모델의 분류 이름이 다른 경우 아래 값을 쉼표로 구분해 지정한다.

```bash
export DOORLOCK_YOLO_FACE_CLASSES=face
export DOORLOCK_YOLO_PHONE_CLASSES="cell phone,phone,screen,tablet,laptop,monitor"
export DOORLOCK_YOLO_OPEN_EYE_CLASSES="open_eye,eye_open,open"
export DOORLOCK_YOLO_CLOSED_EYE_CLASSES="closed_eye,eye_closed,closed"
```

하드웨어 없이 서버 흐름만 확인할 때만 가짜 실행 모드를 사용한다.

```bash
export DOORLOCK_VISION_MOCK=1
python3 server/main.py
```

## 검증

```bash
python3 -B -m unittest discover -s server -p 'test*.py'
```

## 보안 기준

- PIN은 bcrypt로 저장한다.
- 기존 평문 PIN은 일치 확인 후 bcrypt로 승격한다.
- 영상 단계는 YOLO 검사와 얼굴 매칭을 모두 통과해야 한다.
- 휴대폰, 태블릿, 노트북, 모니터류 객체가 감지되면 얼굴 인증을 진행하지 않는다.
- 3회 연속 실패는 대시보드 경고로 표시한다.
- 최근 1시간 실패가 `DOORLOCK_LOCKDOWN_FAILURE_LIMIT` 이상이면 입력을 일시적으로 무시한다.
- 실패 후 재시도 대기 시간은 `DOORLOCK_RATE_LIMIT_SECONDS`로 조정한다.
- 웹 등록은 NFC UID를 대문자 hex로 정규화하고 PIN은 4-8자리 숫자로 제한한다.
- 시리얼 통신은 평문이다. 실제 설치 시 USB와 릴레이 배선은 하우징 안에 둔다.

## 문서

- [시스템 설계](docs/system_design.md)
- [하드웨어 사양](docs/hardware_spec.md)
- [Arduino 설정](docs/arduino_setup.md)
- [배포 가이드](DEPLOYMENT.md)
- [보안 분석](SECURITY_ANALYSIS.md)
- [문제 해결](TROUBLESHOOTING.md)
