---
sidebar_position: 1
---

# 테스트 계획 및 결과 (Test Plan and Results)

이 문서는 2FA Smart Door Lock System의 기능적 정확성을 확인하기 위해 사용된 표준 검증 절차를 간략히 설명한다.

## 단위 테스트 (Unit Testing)

Python Backend는 개별 컴포넌트의 로직을 검증하기 위해 표준 `unittest` 프레임워크를 사용한다. 다음 명령어를 통해 로컬에서 테스트를 실행할 수 있다.

```bash
python3 -B -m unittest discover -s server -p 'test*.py'
```

주요 단위 테스트 적용 범위(Coverage)는 다음과 같다.
- `test_validation.py`: UID 정규화 및 PIN 해싱을 검증한다.
- `test_database*.py`: 동시 쓰기 안전성(Concurrent Write Safety) 및 WAL 모드 구성을 검증한다.
- `test_vision_yolo.py`: 정적 모의(Mock) 이미지를 사용하여 임베딩 추출 배열과 코사인 유사도 논리를 검증한다.

## 시스템 통합 테스트 시나리오 (System Integration Testing / Scenarios)

다음 매트릭스는 통합된 프로토타입에서 수행된 물리적 테스트 시나리오를 나타낸다.

| 테스트 ID (Test ID) | 시나리오 (Scenario) | 절차 (Procedure) | 예상 결과 (Expected Result) | 실제 상태 (Actual Status) |
|---|---|---|---|---|
| INT-01 | 완전 성공 (Full Success) | 유효한 NFC 카드를 제시한다. 등록된 얼굴을 카메라에 제시한다. | 릴레이가 3초 동안 활성화된다. `SUCCESS`가 로깅된다. | 통과 (Pass) |
| INT-02 | 유효하지 않은 1차 인증 (Invalid Primary) | 등록되지 않은 NFC 카드를 제시한다. | 즉시 거부한다. `FAILURE_AUTH1`이 로깅된다. 카메라가 활성화되지 않는다. | 통과 (Pass) |
| INT-03 | 유효한 1차 인증, 유효하지 않은 얼굴 (Valid Primary, Invalid Face) | 유효한 NFC 카드를 제시한다. 등록되지 않은 얼굴을 카메라에 제시한다. | 거부한다. `FAILURE_AUTH2`가 로깅된다. 릴레이가 비활성화 상태를 유지한다. | 통과 (Pass) |
| INT-04 | 유효한 1차 인증, 얼굴 없음 (Valid Primary, No Face) | 유효한 NFC 카드를 제시한다. 카메라 렌즈를 가린다. | 시간 초과(Timeout) 후 거부한다. `FAILURE_TIMEOUT`이 로깅된다. 릴레이가 비활성화 상태를 유지한다. | 통과 (Pass) |
| INT-05 | 하드웨어 연결 끊김 (Hardware Disconnect) | Backend가 실행되는 동안 Arduino USB 연결을 해제한다. | Backend가 우아하게(Gracefully) `serial.SerialException`을 처리하고 재연결을 시도한다. | 통과 (Pass) |

*참고: 물리적 하드웨어 없이 배포된 시스템(예: CI/CD)의 경우, `mock_arduino.py` 스크립트가 시리얼 입력을 시뮬레이션하여 물리적 장비 없이도 Backend 로직을 검증한다.*
