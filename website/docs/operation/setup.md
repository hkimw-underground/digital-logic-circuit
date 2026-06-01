---
sidebar_position: 1
---

# 시스템 설정 및 배포 가이드 (System Setup and Deployment)

본 문서는 2FA Smart Door Lock System의 하드웨어 프로토타입 구성과 소프트웨어 인프라 빌드 및 배포를 위한 표준 절차를 기술한다.

## 저장소 구조 (Repository Structure)

프로젝트는 크게 세 가지 도메인으로 구성된다.
- `/arduino`: 마이크로컨트롤러용 C++ 펌웨어. 현재 시연 기준은 `arduino/doorlock_firmware/doorlock_firmware.ino`이다.
- `/server`: Python FastAPI Backend, SQLite 데이터베이스, OpenCV/YOLOv8 Vision AI 모듈
- `/website`: Docusaurus 기반 기술 문서 및 React 모니터링 대시보드

## 로컬 개발 환경 요구사항 (Prerequisites)

시스템 구축을 위해 다음의 하드웨어 및 소프트웨어 환경이 필요하다.

### 하드웨어 (Hardware)
- **Main Board**: Arduino UNO R4 WiFi
- **Sensors**: MFRC522 RFID 모듈, TTP229 터치 키패드
- **Actuator**: SG-90 서보모터
- **Camera**: 표준 USB 웹캠, IP 카메라, 또는 USB-C로 연결한 ESP32-CAM Serial JPEG 소스

### 소프트웨어 (Software)
- Node.js (v20 이상)
- Python 3.10 이상
- Arduino IDE

## 하드웨어 구성 시 주의사항

물리적 조립 전 다음의 공학적 제약 사항을 반드시 준수해야 한다.
1. **로직 레벨 (Logic Levels)**: MFRC522 모듈은 3.3V 전압에서 동작한다. Arduino의 5V 핀에 직접 연결할 경우 모듈이 손상될 수 있으므로 전압 레벨 변환에 유의한다.
2. **전원 관리 (Power Management)**: Arduino GPIO 핀은 서보나 부저 전원을 직접 공급하지 않는다. 서보/부저는 5V 전원 레일에서 공급하고 모든 GND를 공통으로 묶는다.
3. **Fail-Safe 설계**: 본 시스템은 실험용 프로토타입이다. 실제 보안이 필요한 환경에 적용하기 전, 전원 차단 시 잠금 상태 유지(Fail-Secure) 또는 해제(Fail-Safe) 여부를 하드웨어 특성에 맞춰 검토해야 한다.

## 소프트웨어 설치 및 실행

### 기술 문서 및 대시보드 (Docusaurus)

```bash
cd website
npm install
npm run build
```

### 백엔드 서버 (FastAPI)

의존성 설치가 제한된 환경에서는 시스템 표준 라이브러리를 최대한 활용한다.

```bash
# 가상 환경 활성화
source .venv/bin/activate

# 실제 하드웨어 실행 예시
DOORLOCK_SERIAL_PORT=auto \
DOORLOCK_VISION_MOCK=false \
DOORLOCK_YOLO_ENABLED=false \
python3 server/main.py
```

서버는 `/dev/ttyACM*`, `/dev/ttyUSB*`를 스캔하고 Arduino 펌웨어의 `PING` 응답으로 포트를 식별한다. 카메라/얼굴 등록이 준비되지 않은 상태에서 Serial/서보 동작만 먼저 확인하려면 `DOORLOCK_VISION_MOCK=true`로 실행한다.

ESP32-CAM을 USB-C로 직접 연결하는 경우에는 일반 웹캠처럼 잡히지 않는다. ESP32-CAM에 `esp32cam/serial_camera/serial_camera.ino`를 업로드한 뒤 다음처럼 실행한다.

```bash
DOORLOCK_SERIAL_PORT=auto \
DOORLOCK_CAMERA_URL=serial:auto \
DOORLOCK_ESP32CAM_BAUD_RATE=921600 \
DOORLOCK_VISION_MOCK=false \
DOORLOCK_YOLO_ENABLED=false \
python3 server/main.py
```

### 테스트 및 검증 (Testing)

`unittest` 프레임워크를 통해 Backend 로직을 검증한다.

```bash
source .venv/bin/activate
python3 -B -m unittest discover -s server -p 'test*.py'
```

## 모의 실행 모드 (Mock Execution)

물리적 하드웨어(Arduino, 카메라, 서보)가 없는 CI/CD 환경이나 클라우드 작업 환경에서는 시뮬레이션 모드를 지원한다.

- **Vision AI Mocking**: 환경 변수 `DOORLOCK_VISION_MOCK=1`을 설정하여 카메라 입력 없이 정적 테스트 데이터로 인증 흐름을 검증한다.
- **Hardware Mocking**: `python3 server/fake_arduino.py`를 실행하여 PTY 기반 가상 Serial 장치로 NFC 태그나 PIN 입력을 시뮬레이션한다.

## 배포 및 게시 (GitHub Pages)

문서 사이트는 GitHub Pages를 통해 호스팅된다.
- **Build Source**: `/website` 디렉토리
- **Base URL**: `docusaurus.config.js`의 `/digital-logic-circuit/` 설정 확인
- **접속 주소**: [https://school-project-hwkim-dev.github.io/digital-logic-circuit/](https://school-project-hwkim-dev.github.io/digital-logic-circuit/)

## 최종 점검 체크리스트

커밋 및 병합 전 다음 항목을 확인한다.
- [ ] `npm run build` 실행 시 오류가 없는가?
- [ ] 문서 내 모든 내부 링크와 다이어그램이 정상적으로 렌더링되는가?
- [ ] "TODO" 또는 "Mock"과 같은 임시 텍스트가 공개 문서에 남아있지 않은가?
- [ ] 모든 기술 용어가 프로젝트 표준 용어집과 일치하는가?
