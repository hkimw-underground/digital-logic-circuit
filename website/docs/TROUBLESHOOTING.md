# 문제 해결

설치와 데모 실행 중 자주 확인해야 하는 항목이다.

## 시리얼 포트

증상: `serial.serialutil.SerialException: could not open port`

확인:
- Arduino IDE Serial Monitor가 닫혀 있다.
- `DOORLOCK_SERIAL_PORT`가 실제 보드 포트와 일치한다.
- Windows는 `COMx`, Linux는 `/dev/ttyACM*` 또는 `/dev/ttyUSB*`를 확인한다.

## 카메라

증상: OpenCV가 카메라를 열지 못한다.

확인:
- 카메라가 연결되어 있고 다른 앱이 점유하지 않는다.
- `server/vision_ai.py`의 카메라 index가 실제 장치와 맞는다.
- `DOORLOCK_VISION_MOCK=1`은 소프트웨어 흐름 확인용으로만 사용한다.

## YOLO 모델

증상: 얼굴 대조 전에 영상 검증이 실패한다.

확인:
- `models/doorlock_yolov8n.pt`가 있거나 `DOORLOCK_YOLO_MODEL_PATH`가 올바른 파일을 가리킨다.
- `requirements.txt` 기준으로 `ultralytics`가 설치되어 있다.
- 모델 class 이름이 `DOORLOCK_YOLO_*_CLASSES` 설정과 일치한다.

## 데이터베이스

증상: `sqlite3.OperationalError: database is locked`

확인:
- 운영 서버 프로세스가 하나만 실행 중이다.
- 대시보드와 서버가 같은 `DOORLOCK_DB_PATH`를 사용한다.
- 중복 프로세스를 종료한 뒤 서버를 다시 시작한다.

## NFC 또는 키패드

증상: 카드를 태그하거나 PIN을 입력해도 서버가 반응하지 않는다.

확인:
- 배선이 `docs/hardware_spec.md`와 일치한다.
- Arduino 전원 LED가 켜져 있다.
- Python 서버 실행 전 Serial Monitor에서 `WAKEUP:NFC:<UID>` 또는 `WAKEUP:PW:<PIN>`이 출력된다.
