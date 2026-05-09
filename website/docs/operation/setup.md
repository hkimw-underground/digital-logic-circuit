---
sidebar_position: 1
---

# 시스템 설정 및 배포 가이드 (System Setup and Deployment)

본 문서는 2FA Smart Door Lock System의 하드웨어 프로토타입 구성과 소프트웨어 인프라 빌드 및 배포를 위한 표준 절차를 기술한다.

## 저장소 구조 (Repository Structure)

프로젝트는 크게 세 가지 도메인으로 구성된다.
- `/arduino`: 마이크로컨트롤러용 C++ 펌웨어 (`doorlock.ino`)
- `/server`: Python FastAPI Backend, SQLite 데이터베이스, OpenCV/YOLOv8 Vision AI 모듈
- `/website`: Docusaurus 기반 기술 문서 및 React 모니터링 대시보드

## 로컬 개발 환경 요구사항 (Prerequisites)

시스템 구축을 위해 다음의 하드웨어 및 소프트웨어 환경이 필요하다.

### 하드웨어 (Hardware)
- **Main Board**: Arduino Uno 또는 Nano
- **Sensors**: MFRC522 RFID 모듈, 4x4 Matrix Keypad
- **Actuator**: 5V/12V Relay 모듈 및 도어락 솔레노이드
- **Camera**: 표준 USB 웹캠 (Vision AI용)

### 소프트웨어 (Software)
- Node.js (v20 이상)
- Python 3.10 이상
- Arduino IDE

## 하드웨어 구성 시 주의사항

물리적 조립 전 다음의 공학적 제약 사항을 반드시 준수해야 한다.
1. **로직 레벨 (Logic Levels)**: MFRC522 모듈은 3.3V 전압에서 동작한다. Arduino의 5V 핀에 직접 연결할 경우 모듈이 손상될 수 있으므로 전압 레벨 변환에 유의한다.
2. **전원 격리 (Power Isolation)**: Arduino GPIO 핀은 도어락과 같은 고전류 부하를 직접 구동할 수 없다. 반드시 Relay를 통해 외부 전원과 논리 회로를 격리한다.
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

# 서버 실행
python3 server/main.py
```

### 테스트 및 검증 (Testing)

`unittest` 프레임워크를 통해 Backend 로직을 검증한다.

```bash
source .venv/bin/activate
python3 -B -m unittest discover -s server -p 'test*.py'
```

## 모의 실행 모드 (Mock Execution)

물리적 하드웨어(Arduino, 카메라, 릴레이)가 없는 CI/CD 환경이나 클라우드 작업 환경에서는 시뮬레이션 모드를 지원한다.

- **Vision AI Mocking**: 환경 변수 `DOORLOCK_VISION_MOCK=1`을 설정하여 카메라 입력 없이 정적 테스트 데이터로 인증 흐름을 검증한다.
- **Hardware Mocking**: `python3 server/mock_arduino.py`를 실행하여 NFC 태그나 PIN 입력을 소프트웨어적으로 시뮬레이션한다.

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
