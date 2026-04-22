# 배포 가이드

## 1. 하드웨어
1. [하드웨어 사양](docs/hardware_spec.md)에 맞춰 회로를 배선한다.
2. `arduino/doorlock.ino`를 업로드한다.
3. Serial Monitor를 `9600` baud로 열고 `SYSTEM_READY`를 확인한다.
4. Python 서버 실행 전 Serial Monitor를 닫는다. 시리얼 포트는 한 프로세스만 사용할 수 있다.

## 2. 서버 환경
필요한 라이브러리를 설치한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

소스 파일을 직접 고치지 않고 환경변수로 실행 값을 지정한다.

```bash
export DOORLOCK_SERIAL_PORT=/dev/ttyACM0
export DOORLOCK_BAUD_RATE=9600
export DOORLOCK_DB_PATH=server/doorlock.db
export DOORLOCK_WEB_HOST=127.0.0.1
export DOORLOCK_WEB_PORT=8000
python3 server/main.py
```

Windows 예시:

```powershell
$env:DOORLOCK_SERIAL_PORT="COM3"
$env:DOORLOCK_BAUD_RATE="9600"
python server/main.py
```

## 3. 얼굴 확인 모드
실제 사용 환경에서는 준비가 안 된 상태에서 문을 열지 않는다. YOLO nano 모델, 카메라, `opencv-python`, `ultralytics`, `face_recognition`, 사용자 얼굴 정보 중 하나라도 없으면 문은 잠긴 상태를 유지한다.

기본 YOLO 모델 경로:

```bash
export DOORLOCK_YOLO_MODEL_PATH=models/doorlock_yolov8n.pt
```

nano 모델은 얼굴, 휴대폰이나 화면, 열린 눈, 감긴 눈을 찾을 수 있어야 한다. 모델의 분류 이름이 기본값과 다르면 `DOORLOCK_YOLO_FACE_CLASSES`, `DOORLOCK_YOLO_PHONE_CLASSES`, `DOORLOCK_YOLO_OPEN_EYE_CLASSES`, `DOORLOCK_YOLO_CLOSED_EYE_CLASSES`를 지정한다.

데모 모드:

```bash
export DOORLOCK_VISION_MOCK=1
python3 server/main.py
```

데모 모드는 하드웨어 없이 서버 흐름만 확인할 때 사용한다. 실제 설치 환경에서는 쓰지 않는다.

## 4. 실행
`server/main.py`는 시리얼 수신과 웹 화면을 함께 실행한다.

```bash
python3 server/main.py
```

대시보드:
- `server/cert.pem`, `server/key.pem`이 있으면 `https://localhost:8000`
- 인증서가 없으면 `http://localhost:8000`

다른 장비에서 접속해야 하면 `DOORLOCK_WEB_HOST=0.0.0.0`으로 바인딩하고, 방화벽과 네트워크 접근 범위를 별도로 제한한다.

`server/app.py`는 이전 Flask 화면이다. 현재 실행 기준은 `server/main.py`다.

## 5. 사용자 등록
1. 대시보드를 연다.
2. 사용자 추가 화면으로 이동한다.
3. 얼굴 정보를 캡처한다.
4. 이름, NFC UID, PIN을 입력한다.
5. 등록한다.

PIN은 bcrypt로 저장한다. 기존 평문 PIN은 일치 확인 후 bcrypt로 승격한다.

## 6. 운영 체크리스트
- `DOORLOCK_VISION_MOCK`는 설정하지 않거나 `0`으로 둔다.
- `DOORLOCK_ALLOW_UNENROLLED_FACE`는 설정하지 않거나 `0`으로 둔다.
- `DOORLOCK_YOLO_MODEL_PATH`는 로컬 디스크의 학습된 nano 모델 파일을 가리킨다.
- 데이터베이스 파일은 공개 웹 경로 밖에 두고 소유자만 접근할 수 있게 설정한다.
- Arduino, 릴레이, USB 케이블, 잠금장치 배선은 외부에서 접근하기 어려운 하우징 안에 둔다.
- Arduino IDE Serial Monitor가 시리얼 포트를 점유하지 않는다.
- 최소 한 명 이상의 사용자가 얼굴 정보까지 등록되어 있다.
