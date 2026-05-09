---
sidebar_position: 3
---

# 시리얼 통신 프로토콜 (Serial Communication Protocol)

본 시스템은 Arduino와 백엔드 서버 간의 데이터 교환을 위해 USB Serial 인터페이스를 기반으로 하는 경량 텍스트 프로토콜을 사용한다. 이 프로토콜은 인증 장치(Arduino)와 제어 로직(Python 서버) 사이의 통신 규약을 정의한다.

## 통신 설정 (Serial Configuration)

안정적인 데이터 송수신을 위해 다음과 같은 시리얼 통신 설정을 유지한다.

- **Baud Rate**: 9600 bps
- **Data Bits**: 8 bits
- **Parity**: None
- **Stop Bits**: 1 bit
- **Termination**: Line Feed (`\n`)

## 메시지 형식 (Message Formats)

### 1. Arduino → 백엔드 서버 (이벤트 알림)

Arduino는 하드웨어 인터럽트 및 사용자 입력을 감지하여 서버로 상태를 보고한다. 1차 인증(NFC/PIN) 시에는 서버의 절전 상태나 대기 모드를 고려하여 `WAKEUP` 접두사를 포함한 정형화된 형식을 사용한다.

| 이벤트 | 메시지 형식 | 설명 |
| :--- | :--- | :--- |
| 시스템 준비 | `SYSTEM_READY` | Arduino 부팅 및 초기화 완료 시 송신 |
| NFC 태그 감지 | `WAKEUP:NFC:[UID]` | 감지된 NFC 카드의 고유 식별자(HEX) 전송 |
| 비밀번호 입력 | `WAKEUP:PW:[PIN]` | 키패드로 입력된 비밀번호 문자열 전송 |
| 도어 개방 완료 | `DOOR_OPENED` | 릴레이 활성화를 통한 잠금 해제 상태 보고 |
| 도어 폐쇄 완료 | `DOOR_CLOSED` | 설정된 시간이 경과하여 잠금 상태로 복귀 보고 |

### 2. 백엔드 서버 → Arduino (제어 명령)

백엔드 서버는 2차 인증 결과를 바탕으로 Arduino에 하드웨어 제어 명령을 하달한다.

| 명령 | 메시지 형식 | 동작 |
| :--- | :--- | :--- |
| 잠금 해제 | `OPEN_DOOR` | 릴레이를 활성화하여 물리적 잠금을 해제함 |

## 통신 흐름 예시 (Sequence Example)

1.  **초기화**: Arduino 전원 투입 → `SYSTEM_READY` 송신
2.  **1차 인증 요청**: 사용자가 NFC 태그 → `WAKEUP:NFC:A1B2C3D4` 송신
3.  **서버 판단**: 서버에서 NFC 일치 여부 확인 후 얼굴 인식(2차 인증) 수행
4.  **제어 명령**: 인증 성공 시 서버에서 `OPEN_DOOR` 송신
5.  **상태 피드백**: Arduino 릴레이 작동 → `DOOR_OPENED` 송신 → 3초 후 `DOOR_CLOSED` 송신

## 보안 및 설계 고려사항

- **무결성**: 현재 프로토콜은 일반 텍스트 기반으로, 물리적 Serial 연결의 보안이 확보된 환경을 가정한다.
- **확장성**: `WAKEUP:[TYPE]:[VALUE]` 구조를 채택하여, 향후 지문 인식이나 기타 생체 인증 수단 추가 시 TYPE 필드 확장이 용이하다.
- **Fail-Secure**: 서버와의 연결이 끊기거나 명령이 도달하지 않을 경우, Arduino는 기본적으로 `LOCKED` 상태를 유지하여 보안성을 확보한다.
