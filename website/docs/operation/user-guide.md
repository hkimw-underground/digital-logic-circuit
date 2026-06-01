---
sidebar_position: 2
---

# 사용자 가이드 및 운영 (User Guide and Operation)

이 문서는 2FA Smart Door Lock System의 표준 운영 절차와 인증 흐름을 최종 사용자와 관리자 관점에서 설명한다.

## 시스템 시작 절차 (System Startup)

시스템을 가동하기 위해 다음 단계를 순차적으로 수행한다.

1.  **전원 공급**: Arduino, 5V 전원 레일, 3.3V NFC 전원 레일, 공통 GND가 올바르게 연결되었는지 확인한다.
2.  **Backend 실행**: 서버 환경에서 Python FastAPI 서버(`server/main.py`)를 시작한다. 시작 시 SQLite 데이터베이스가 자동으로 점검 및 초기화된다.
3.  **Serial Handshake**: Arduino가 연결되면 `SYSTEM_READY` 신호를 Backend에 전송한다. Backend는 이 신호를 수신한 후 실시간 폴링 루프를 시작한다.
4.  **Vision AI 모드 확인**: 실제 얼굴 인증은 `DOORLOCK_VISION_MOCK=false`로 실행한다. YOLO 모델이 준비되지 않은 시연에서는 `DOORLOCK_YOLO_ENABLED=false`로 고정한다.

## 인증 프로세스 (Authentication Flow)

최종 사용자는 다음의 2단계 인증 과정을 통해 출입 권한을 획득한다.

### 1단계: 1차 인증 (NFC 또는 PIN)
-   **NFC**: 등록된 카드를 MFRC522 리더기에 탭한다.
-   **PIN**: TTP229 키패드에서 4자리 이상 숫자를 입력한다. 현재 8키 모드 펌웨어는 4자리 이상 입력 시 자동으로 PIN을 전송한다.
-   1차 인증 정보가 데이터베이스와 일치하면 즉시 2단계 인증으로 전환된다.

### 2단계: 2차 인증 (얼굴 인식)
-   카메라 렌즈를 정면으로 응시한다.
-   Vision AI 모듈이 사용자의 얼굴을 캡처하고 등록된 얼굴 인코딩과 비교한다.
-   임계값 이상의 유사도가 감지되면 인증이 승인된다.

### 3단계: 잠금 해제 (Unlock)
-   인증 성공 시 Backend가 Arduino로 `OPEN_DOOR` 명령을 전송한다.
-   Arduino는 SG-90 서보를 열림 각도(`90도`)로 이동시킨다.
-   시간이 경과하면 서보가 잠김 각도(`0도`)로 자동 복귀한다.

## 실패 처리 및 로깅 (Error Handling)

모든 인증 시도는 SQLite 데이터베이스에 기록되며, 실패 시 시스템은 보안을 위해 잠금 상태를 유지한다.

| 구분 | 이벤트 로그 | 설명 |
| :--- | :--- | :--- |
| **1차 인증 성공** | `1ST_AUTH_SUCCESS` | 등록된 NFC 또는 PIN이 확인됨 |
| **최종 인증 성공** | `FINAL_SUCCESS` | 1차 인증과 얼굴 인증이 모두 통과됨 |
| **1차 인증 실패** | `UNAUTHORIZED` | 등록되지 않은 카드 또는 잘못된 PIN 입력 |
| **2차 인증 실패** | `FINAL_FAIL` | 얼굴 불일치, 카메라 오류, 또는 얼굴 정보 없음 |

## 안전 및 주의사항 (Safety and Precautions)

-   **Fail-Secure 원칙**: 전원 차단, 시스템 오류 또는 통신 단절 시 서버가 `OPEN_DOOR`를 보내지 않으므로 서보는 잠금 상태를 유지한다.
-   **조명 환경**: 얼굴 인식의 정확도는 조도에 영향을 받으므로, 너무 어둡거나 강한 역광이 있는 장소에서의 사용은 권장하지 않는다.
-   **비상 개방**: 전자적 고장 상황을 대비하여 물리적 열쇠나 수동 개폐 장치를 별도로 구비해야 한다.

## 개발자 모드 (Mock Execution)

물리적 하드웨어가 없는 환경에서는 다음과 같이 시뮬레이션할 수 있다.

1.  Backend 서버를 실행한다.
2.  `python3 server/fake_arduino.py`를 실행하여 가상의 Serial 장치를 만든다.
3.  출력된 `/dev/pts/XX` 값을 `DOORLOCK_SERIAL_PORT`에 넣고 Backend를 실행한다.
4.  CLI 메뉴를 통해 NFC UID 또는 PIN을 입력하여 전체 2FA 로직의 동작 여부를 검증한다.

## 운영 한계점 (Operational Limitations)

-   **단일 노드**: 현재 감사 로그는 Backend 서버의 로컬 데이터베이스에 저장된다.
-   **안티 스푸핑(Anti-Spoofing)**: 일반 RGB 카메라를 사용하므로 고해상도 사진이나 디스플레이를 이용한 2D 스푸핑 공격에 취약할 수 있다.
