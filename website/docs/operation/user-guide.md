---
sidebar_position: 2
---

# 사용자 가이드 및 운영 (User Guide and Operation)

이 문서는 최종 사용자와 관리자 관점에서 2FA Smart Door Lock System의 표준 운영 절차와 예상되는 동작을 자세히 설명한다.

## 시스템 시작 순서 (System Startup Sequence)

1. **전원 초기화 (Power Initialization)**: Arduino와 독립된 잠금장치 전원 공급 장치에 전원이 켜져 있는지 확인한다.
2. **백엔드 초기화 (Backend Initialization)**: Python FastAPI 서버(`server/main.py`)를 시작한다. 서버는 SQLite 데이터베이스가 없는 경우 자동으로 초기화한다.
3. **시리얼 핸드셰이크 (Serial Handshake)**: 시작 시 Arduino는 USB 시리얼 연결을 통해 `SYSTEM_READY` 신호를 브로드캐스트(Broadcast)한다. Backend는 이 신호를 확인하고 폴링 루프(Polling Loop)를 시작한다.
4. **비전 모듈 준비 (Vision Module Warm-up)**: YOLOv8 모델이 메모리에 로드된다. Backend 로그에 카메라 화면이 성공적으로 캡처되었다고 표시되면 시스템이 완전히 작동하는 것이다.

## 인증 흐름 (최종 사용자) (Authentication Flow / End-User)

접근 권한을 얻으려면 등록된 사용자가 2FA 파이프라인을 성공적으로 완료해야 한다.

### 1단계: 1차 인증 (NFC 또는 PIN) (Step 1: Primary Authentication)
사용자는 등록된 자격 증명을 로컬 하드웨어에 제시하여 프로세스를 시작한다.
- **NFC 방식**: 등록된 13.56MHz 카드를 MFRC522 리더에 탭(Tap)한다.
- **PIN 방식**: 매트릭스 키패드를 사용하여 등록된 4자리 코드를 입력한 후, 특정 종료 키(예: 구성에 따라 `#` 또는 `A`)를 누른다.

*1차 자격 증명이 유효하면 시스템은 즉시 2단계로 넘어간다.*

### 2단계: 2차 인증 (얼굴 인식) (Step 2: Secondary Authentication)
1차 인증이 성공하면 Backend는 Vision 모듈을 활성화한다.
- 사용자는 카메라의 시야각(Field of View) 안에 서 있어야 한다.
- 시스템은 프레임을 캡처하고, YOLOv8을 통해 얼굴 임베딩(Face Embeddings)을 추출하며, 1차 자격 증명과 연결된 저장된 프로필과 비교한다.

### 3단계: 릴레이 잠금 해제 동작 (Step 3: Relay Unlock Behavior)
- 얼굴 검증 결과가 긍정적(일치)이면, Backend는 시리얼을 통해 명시적인 `UNLOCK` 명령을 전송한다.
- Arduino는 릴레이 핀을 토글(Toggle)하여 사전 구성된 시간(기본값: 3000ms) 동안 잠금 메커니즘에 전원을 공급하여 물리적 출입을 허용한다.
- 시간 초과(Timeout)가 만료되면 시스템은 즉시 다시 잠긴다.

## 실패 처리 및 로깅 (Failure Handling and Logging)

이 시스템은 어떤 실패가 발생하더라도 안전한 잠금 상태를 유지하도록 설계되었다. 모든 인증 시도는 SQLite `access_logs` 테이블에 변경할 수 없게(Immutably) 로깅된다.

- **1차 실패 (Primary Failure)**: 등록되지 않은 NFC 카드가 태그되거나 잘못된 PIN이 입력되면, 해당 이벤트는 `FAILURE_AUTH1`로 기록된다. Vision 모듈은 작동하지 않는다.
- **2차 실패 (Secondary Failure)**: 1차 자격 증명은 유효하지만 카메라가 일치하지 않는 얼굴, 여러 얼굴을 감지하거나 지정된 시간 내에 얼굴을 감지하지 못하면 이벤트는 `FAILURE_AUTH2`로 기록된다. 문은 잠긴 상태를 유지한다.
- **하드웨어 연결 끊김 (Hardware Disconnect)**: Arduino와의 시리얼 연결이 끊어지면 Backend는 치명적인 시스템 오류를 기록한다. `UNLOCK` 명령이 없는 Arduino는 릴레이를 비활성화된 상태로 유지한다.

## 대시보드 모니터링 (Dashboard Monitoring)

관리자는 웹 대시보드(Web Dashboard)를 통해 시스템 성능을 모니터링하고 감사 로그(Audit Logs)를 확인할 수 있다.
- 배포된 Docusaurus 사이트의 **검증 상태** 페이지로 이동한다.
- 대시보드는 총 인증 시도 횟수, 성공/실패 비율, 그리고 정적 검증 데이터 세트를 기반으로 한 실패 원인 분포에 대한 요약을 제공한다.

## 수동 검증 (모의 모드) (Manual Validation / Mock Mode)

물리적 하드웨어가 없는 개발 또는 시연 목적의 경우:
1. Backend가 실행 중인지 확인한다.
2. 별도의 터미널에서 `python3 server/mock_arduino.py`를 실행한다.
3. CLI 프롬프트를 사용하여 시뮬레이션된 NFC UID 또는 PIN 코드를 주입한다.
4. Backend 로그를 관찰하여 2단계 검증 논리와 시뮬레이션된 `UNLOCK` 명령의 올바른 전송을 확인한다.

## 알려진 운영 한계점 (Known Operational Limitations)

- **조명 의존성 (Lighting Dependency)**: 얼굴 검증 모듈은 표준 RGB 웹캠을 사용하므로 저조도 환경에서는 정확도가 저하된다.
- **단일 노드 로깅 (Single Node Logging)**: 감사 로그(Audit Logs)는 Python Backend가 실행되는 호스트 장비에 로컬로 저장된다. 현재 다중 도어(Multi-door) 동기화는 지원되지 않는다.
