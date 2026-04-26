# Arduino 설정 가이드

## 필요 라이브러리
- `MFRC522`
- `Keypad` by Mark Stanley and Alexander Brevig

## 펌웨어
`arduino/doorlock.ino`를 업로드한다. `arduino/doorlock_firmware.ino`는 호환용 사본이며, 기준 파일은 `doorlock.ino`다.

## 배선
[하드웨어 사양](hardware_spec.md)의 핀맵을 사용한다. 핵심 제약은 다음과 같다.

- MFRC522는 하드웨어 SPI 핀 D10, D11, D12, D13을 사용한다.
- 키패드는 D2-D8과 A0을 사용한다.
- 릴레이 신호선은 A1을 사용한다.
- MFRC522 reset은 A2를 사용한다.

이 배치는 릴레이 제어가 SPI SCK 또는 키패드 핀과 겹치는 문제를 피한다.

## 업로드 절차
1. Arduino IDE에서 `arduino/doorlock.ino`를 연다.
2. 보드와 포트를 선택한다. R4 Minima를 사용하는 경우 Arduino UNO R4 Minima를 선택한다.
3. Library Manager에서 누락된 라이브러리를 설치한다.
4. 스케치를 업로드한다.
5. Serial Monitor를 `9600` baud로 연다.
6. reset 후 `SYSTEM_READY`가 출력되는지 확인한다.

## 프로토콜 확인
| 동작 | 예상 시리얼 출력 |
| --- | --- |
| 등록된 NFC 카드 태그 | `WAKEUP:NFC:<UID>` |
| 4자리 PIN 입력 | `WAKEUP:PW:<PIN>` |
| 서버가 `OPEN_DOOR` 전송 | `DOOR_OPENED`, 3초 뒤 `DOOR_CLOSED` |

릴레이 타이머는 기다리는 동안 입력 처리를 멈추지 않는 방식이다. 문이 열린 상태에서도 NFC와 키패드 입력은 계속 응답한다.
