---
sidebar_position: 2
---

# 배선 및 핀 맵

현재 배선 기준은 `arduino/doorlock_firmware/doorlock_firmware.ino`이다. `arduino/doorlock.ino`의 릴레이/4x4 매트릭스 키패드 기준 핀맵은 레거시이므로 사용하지 않는다.

## 최종 핀 맵

| Arduino UNO R4 WiFi 핀 | 연결 대상 | 전압/경유 | 코드 기준 |
|---|---|---|---|
| `D2` | TTP229 `SDO` | 직접 연결 | `KP_SDO_PIN` |
| `D3` | TTP229 `SCL` | 직접 연결 | `KP_SCL_PIN` |
| `D5` | SG-90 서보 신호선 | 직접 연결 | `SERVO_PIN` |
| `A2` | FQ-030 부저 신호선 | 직접 연결 | `BUZZER_IO_PIN` |
| `D9` | MFRC522 `RST` | 레벨 시프터 경유 | `NFC_RST_PIN` |
| `D10` | MFRC522 `SDA/SS` | 레벨 시프터 경유 | `NFC_SS_PIN` |
| `D11` | MFRC522 `MOSI` | 레벨 시프터 경유 | SPI MOSI |
| `D12` | MFRC522 `MISO` | 직접 연결 | SPI MISO |
| `D13` | MFRC522 `SCK` | 레벨 시프터 경유 | SPI SCK |
| `5V` | 5V 레일 | 전원 | TTP229, 서보, 부저, 시프터 HV |
| `3.3V` | 3.3V 레일 | 전원 | MFRC522, 시프터 LV |
| `GND` | GND 레일 | 공통 접지 | 모든 모듈 |

## MFRC522 NFC 배선

| MFRC522 핀 | Arduino 연결 | 비고 |
|---|---|---|
| `SDA/SS` | `D10` | 레벨 시프터 경유 |
| `SCK` | `D13` | 레벨 시프터 경유 |
| `MOSI` | `D11` | 레벨 시프터 경유 |
| `MISO` | `D12` | 현재 기준 직결 |
| `RST` | `D9` | 레벨 시프터 경유 |
| `IRQ` | 연결 안 함 | 코드에서 미사용 |
| `GND` | GND 레일 | 공통 접지 |
| `3.3V` | 3.3V 레일 | 5V 금지 |

레벨 시프터는 2채널 모듈 2개를 사용한다. 두 모듈 모두 `HV=5V`, `LV=3.3V`, `GND=공통`을 연결해야 한다.

## TTP229 키패드 배선

| TTP229 핀 | Arduino 연결 |
|---|---|
| `VCC` | 5V 레일 |
| `GND` | GND 레일 |
| `SDO` | `D2` |
| `SCL` | `D3` |

현재 펌웨어는 8키 모드 기준이다. TP2를 GND에 쇼트해 16키 모드를 사용할 경우 펌웨어의 키 매핑도 함께 수정해야 한다.

## 서보 및 부저 배선

| 부품 | 전원 | GND | 신호 |
|---|---|---|---|
| SG-90 서보 | 5V 레일 | GND 레일 | `D5` |
| FQ-030 수동 부저 | 5V 레일 | GND 레일 | `A2` |

서보가 떨리거나 Arduino가 재부팅되면 전원 부족을 먼저 확인한다. 외부 5V 전원을 사용할 경우 Arduino USB 5V와 같은 레일에 무작정 병렬 연결하지 않는다.

## 실행 전 확인

1. 업로드 대상 스케치가 `arduino/doorlock_firmware/doorlock_firmware.ino`인지 확인한다.
2. Arduino 보드 선택이 UNO R4 WiFi인지 확인한다.
3. Serial Monitor 9600 baud에서 `SYSTEM_READY`가 보이는지 확인한다.
4. 서버 실행 시 `DOORLOCK_SERIAL_PORT`를 실제 Arduino 포트로 고정한다.
