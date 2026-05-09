---
sidebar_position: 1
---

# 테스트 계획 및 결과 (Test Plan and Results)

본 문서는 2FA 스마트 도어락 시스템의 신뢰성과 안전성을 보장하기 위해 수행된 테스트 절차와 결과를 기술한다. 검증 과정은 개별 모듈 단위의 로직 검증부터 실제 하드웨어 통합 시나리오까지 단계적으로 수행되었다.

## 1. 테스트 환경 (Testing Environment)

시스템 검증은 하드웨어와 소프트웨어가 통합된 실제 실험 환경 및 CI(Continuous Integration) 기반의 가상 환경에서 병행되었다.

### 1.1 하드웨어 구성
- **Microcontroller**: Arduino Uno (Atmega328P)
- **Primary Auth**: RC522 NFC Reader, 4x4 Matrix Keypad
- **Secondary Auth**: USB 웹캠 (Standard 1080p)
- **Output**: 5V 릴레이 모듈, 전자기 잠금장치 (Solenoid Lock)

### 1.2 소프트웨어 구성
- **OS**: Ubuntu 22.04 LTS / macOS
- **Language**: Python 3.10+, C++ (Arduino IDE)
- **Framework**: FastAPI (Web API), OpenCV & YOLOv8 (Vision AI)
- **Database**: SQLite3 (WAL mode enabled)

## 2. 단위 테스트 (Unit Testing)

백엔드 서버의 핵심 로직은 `unittest` 프레임워크를 통해 독립적으로 검증되었다. 특히 하드웨어 의존성이 있는 부분은 Mocking 기법을 사용하여 격리된 환경에서 테스트를 수행했다.

```bash
# 단위 테스트 실행 명령어
python3 -B -m unittest discover -s server -p 'test*.py'
```

| 테스트 모듈 | 검증 내용 |
|---|---|
| `test_validation.py` | NFC UID 정규화 형식 및 PIN 번호 해싱(Bcrypt) 로직 검증 |
| `test_database.py` | SQLite WAL 모드 설정, 외래 키 제약 조건 및 데이터 무결성 검증 |
| `test_vision_yolo.py` | 얼굴 감지 임계값 처리 및 임베딩 비교 로직의 정확성 검증 |
| `test_notifier.py` | 보안 이벤트 발생 시 Discord Webhook 알림 전송 로직 검증 |
| `test_security_redaction.py` | 로그 및 터미널 출력 시 민감 정보(PIN, UID 일부) 마스킹 처리 검증 |

## 3. 시스템 통합 테스트 (System Integration Testing)

하드웨어와 소프트웨어가 결합된 상태에서 사용자의 실제 이용 흐름을 시뮬레이션하여 전체 시스템의 동작을 검증했다.

| ID | 시나리오 | 테스트 절차 | 예상 결과 | 결과 |
|---|---|---|---|---|
| **ST-01** | 정상 인증 (NFC) | 등록된 NFC 카드 태그 → 등록된 사용자 얼굴 제시 | 잠금 해제 (릴레이 3s 활성화) 및 성공 로그 기록 | 통과 |
| **ST-02** | 정상 인증 (PIN) | 등록된 PIN 번호 입력 → 등록된 사용자 얼굴 제시 | 잠금 해제 (릴레이 3s 활성화) 및 성공 로그 기록 | 통과 |
| **ST-03** | 1차 인증 실패 | 등록되지 않은 NFC 카드 또는 잘못된 PIN 입력 | 즉시 거부, 경고 문구 출력 및 카메라 미작동 | 통과 |
| **ST-04** | 2차 인증 실패 | 유효한 1차 인증 완료 → 미등록 사용자 얼굴 제시 | 접근 거부, 보안 경고 알림 전송 및 로그 기록 | 통과 |
| **ST-05** | 인증 시간 초과 | 1차 인증 후 2차 인증(얼굴) 없이 대기 | 일정 시간 후 세션 종료 및 초기 상태 전환 | 통과 |
| **ST-06** | 하드웨어 복구 | 실행 중 Arduino USB 케이블 분리 후 재연결 | 서버의 자동 재연결 시도 및 통신 복구 확인 | 통과 |

## 4. 예외 및 보안 테스트 (Edge Case & Security Testing)

실제 운영 환경에서 발생할 수 있는 이상 현상에 대한 대응력을 측정했다.

- **무차별 대입 공격 방어**: 잘못된 PIN 입력을 단기간에 반복 시도할 경우, `RATE_LIMIT` 로직에 의해 일정 시간 동안 입력을 차단하는 것을 확인했다.
- **데이터베이스 안정성**: 급격한 전원 차단 상황을 가정하여 데이터베이스 파일의 손상 여부를 확인했으며, WAL 모드를 통해 데이터 무결성이 유지됨을 검증했다.
- **실시간 모니터링**: 관리자 대시보드를 통해 실시간으로 접근 기록과 카메라 피드가 지연 없이 전송되는지 확인했다.

---
*참고: 물리적 하드웨어 장치가 없는 환경(CI/CD 등)에서는 `mock_arduino.py`를 활용하여 시리얼 통신 프로토콜을 시뮬레이션함으로써 로직의 정교함을 검증한다.*
