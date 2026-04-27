---
sidebar_position: 3
---

# 시리얼 프로토콜 (Serial Protocol)

Arduino와 Backend 서버 간의 통신은 USB를 통한 간단한 일반 텍스트(Plaintext) 시리얼 프로토콜(9600 Baud)을 사용한다.

## 메시지 형식 (Message Formats)

### Arduino → Server

| 이벤트 (Event) | 문자열 형식 (String Format) | 예시 (Example) |
|---|---|---|
| 시스템 준비 (System Ready) | `SYSTEM_READY` | `SYSTEM_READY` |
| NFC 카드 탭 (NFC Card Tap) | `UID:<hex_string>` | `UID:A1B2C3D4` |
| PIN 입력 (PIN Entry) | `PIN:<string>` | `PIN:1234` |

### Server → Arduino

| 명령 (Command) | 동작 (Action) |
|---|---|
| `UNLOCK` | 설정된 잠금 해제 시간(예: 3000ms) 동안 릴레이 핀을 HIGH/LOW로 당기도록 Arduino에 지시한다. |
| `DENY` | 명시적인 거부 명령. 오류 비프음 또는 LED 깜박임을 트리거한다(구현된 경우). 릴레이 상태는 잠긴 상태로 유지된다. |

*보안 참고 사항: 이 프로토콜은 현재 암호화되어 있지 않다. 물리적 접근 제한에 관해서는 보안(Security) 섹션을 참조한다.*
