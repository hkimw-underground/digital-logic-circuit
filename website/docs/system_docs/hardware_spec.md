# 하드웨어 사양

## 대상 보드
Arduino Uno, Nano, R4 Minima의 UNO 계열 핀 배치를 기준으로 한다. SPI 핀은 보드 고정 핀이므로 MFRC522와 공유하지 않는다.

## 핀맵
| 부품 | 신호 | Arduino 핀 | 비고 |
| --- | --- | --- | --- |
| MFRC522 | SDA / SS | D10 | SPI slave select |
| MFRC522 | SCK | D13 | 하드웨어 SPI |
| MFRC522 | MOSI | D11 | 하드웨어 SPI |
| MFRC522 | MISO | D12 | 하드웨어 SPI |
| MFRC522 | RST | A2 | 키패드와 충돌하지 않도록 A2 사용 |
| Keypad | Row 1-4 | D2, D3, D4, D5 | 행 입력 |
| Keypad | Col 1-4 | D6, D7, D8, A0 | 열 입력 |
| Relay | Signal | A1 | 기본값: `LOW` 잠금, `HIGH` 열림 |

릴레이 모듈이 active-low이면 `arduino/doorlock.ino`의 `RELAY_LOCKED`, `RELAY_UNLOCKED` 값을 서로 바꾼다.

## 시리얼 프로토콜
| 방향 | 메시지 | 설명 |
| --- | --- | --- |
| Arduino -> 서버 | `SYSTEM_READY` | 펌웨어 부팅 완료 |
| Arduino -> 서버 | `WAKEUP:NFC:<UID>` | NFC UID 전송. 예: `WAKEUP:NFC:A1B2C3D4` |
| Arduino -> 서버 | `WAKEUP:PW:<PIN>` | 키패드 PIN 전송. 예: `WAKEUP:PW:1234` |
| 서버 -> Arduino | `OPEN_DOOR` | 입력 loop를 막지 않고 `DOOR_OPEN_MS` 동안 릴레이 열림 |
| Arduino -> 서버 | `DOOR_OPENED` | 릴레이가 열린 상태로 전환됨 |
| Arduino -> 서버 | `DOOR_CLOSED` | 릴레이가 잠긴 상태로 복귀함 |

`ACTION:OPEN`은 이전 펌웨어와의 호환을 위해 수신만 지원한다. 새 서버는 `OPEN_DOOR`를 전송한다.

## 전기적 주의사항
- Arduino와 릴레이 전원 GND를 공통 접지로 묶는다.
- 솔레노이드 또는 전자석은 Arduino 5V 핀에서 직접 구동하지 않는다. 별도 전원과 릴레이/드라이버를 사용한다.
- USB 시리얼과 릴레이 배선은 잠금형 하우징 안에 넣는다. 현재 프로토콜은 평문이므로 물리적 접근을 제한해야 한다.
