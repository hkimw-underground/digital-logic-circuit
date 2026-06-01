# 하드웨어 부품 명세서

이 문서는 2FA 스마트 도어락 캡스톤 프로토타입의 하드웨어 부품, 전원 조건, 배선 기준, 코드 연결 지점을 한곳에 정리한 기준 문서이다.

## 기준 범위

현재 조립 및 시연 기준은 다음 파일과 설정을 따른다.

| 구분 | 기준 |
|---|---|
| 주 펌웨어 | `arduino/doorlock_firmware/doorlock_firmware.ino` |
| 보드 | Arduino UNO R4 WiFi |
| 서버 통신 | USB Serial, `9600` baud |
| 1차 인증 | MFRC522 NFC 또는 TTP229 PIN |
| 2차 인증 | Python 서버의 카메라/YOLO/face_recognition 또는 mock 모드 |
| 구동부 | SG-90 서보모터, `D5`, 잠김 `0도`, 열림 `90도` |
| 피드백 | FQ-030 수동 부저, `A2` |

루트의 `arduino/doorlock.ino`와 `arduino/doorlock_firmware.ino`는 이전 실험용 스케치가 남아 있는 상태다. 이 문서는 현재 하드웨어 시연용 스케치인 `arduino/doorlock_firmware/doorlock_firmware.ino`를 우선 기준으로 삼는다.

## 전체 구성 요약

| 계층 | 부품 | 프로젝트 역할 | 주요 연결 |
|---|---|---|---|
| 서버 | PC 또는 Raspberry Pi | DB, 웹 UI, 얼굴 인증, 최종 승인 판단 | Arduino와 USB Serial |
| MCU | Arduino UNO R4 WiFi | NFC/PIN 입력 수집, 서보/부저 제어 | USB-C, `D2`, `D3`, `D5`, `A2`, `D9-D13` |
| NFC | RFID-RC522 / MFRC522 | NFC UID 읽기 | SPI, 3.3V, 레벨 시프터 사용 |
| PIN | TTP229 터치 키패드 | PIN 입력 | `SDO -> D2`, `SCL -> D3` |
| 구동 | SG-90 서보모터 | 잠금/해제 동작 | 신호 `D5`, 전원 5V |
| 피드백 | FQ-030 수동 부저 | 키 입력/성공/실패/Lockdown 소리 | 신호 `A2`, 전원 5V |
| 전압 변환 | 2채널 TTL 레벨 시프터 2개 | Arduino 5V 신호를 MFRC522 3.3V 신호로 변환 | 총 4채널 |
| 카메라 | USB 카메라, IP 카메라, 또는 ESP32-CAM USB-Serial | 얼굴 인증 영상 입력 | Python 서버 설정으로 연결 |
| 배선 | MB-102 브레드보드, 점퍼선 | 전원 분배 및 신호 연결 | 5V/GND/3.3V 레일 분리 |

## 최종 핀 맵

| Arduino 핀 | 코드 상수 | 연결 부품 | 방향 | 전압 | 비고 |
|---|---|---|---|---|---|
| `D2` | `KP_SDO_PIN` | TTP229 `SDO` | Keypad -> Arduino | 5V 로직 | `INPUT_PULLUP` |
| `D3` | `KP_SCL_PIN` | TTP229 `SCL` | Arduino -> Keypad | 5V 로직 | 기본 HIGH, 클럭 펄스 |
| `D5` | `SERVO_PIN` | SG-90 주황/노랑 신호선 | Arduino -> Servo | 5V PWM 신호 | `Servo.write(0/90)` |
| `A2` | `BUZZER_IO_PIN` | FQ-030 `I/O` | Arduino -> Buzzer | 5V 로직 | `tone()` 출력 |
| `D9` | `NFC_RST_PIN` | MFRC522 `RST` | Arduino -> NFC | 5V -> 3.3V | 레벨 시프터 경유 |
| `D10` | `NFC_SS_PIN` | MFRC522 `SDA/SS` | Arduino -> NFC | 5V -> 3.3V | 레벨 시프터 경유 |
| `D11` | SPI MOSI | MFRC522 `MOSI` | Arduino -> NFC | 5V -> 3.3V | 레벨 시프터 경유 |
| `D12` | SPI MISO | MFRC522 `MISO` | NFC -> Arduino | 3.3V | 현재 배선은 직결 |
| `D13` | SPI SCK | MFRC522 `SCK` | Arduino -> NFC | 5V -> 3.3V | 레벨 시프터 경유 |
| `A5` | `LED_STATUS_PIN` | 상태 LED | Arduino -> LED | 5V | 코드상 비활성, `LED_ACTIVE=false` |

## 전원 설계 기준

| 전원 레일 | 연결 대상 | 주의사항 |
|---|---|---|
| 5V | Arduino 5V, TTP229 VCC, SG-90 VCC, FQ-030 VCC, 레벨 시프터 HV | 서보 구동 시 순간 전류가 커진다. 외부 5V 전원 사용 시 Arduino GND와 공통 접지 필요 |
| 3.3V | MFRC522 VCC, 레벨 시프터 LV | MFRC522에는 5V를 직접 넣지 않는다 |
| GND | 모든 부품의 GND | 신호 기준점이므로 모든 GND를 반드시 공통 연결 |

권장 전원 여유는 5V 2A 이상이다. USB 포트만으로도 단순 입력 테스트는 가능하지만, 서보가 움직일 때 전압 강하가 발생하면 Arduino 재부팅, 부저 음량 저하, NFC 인식 불량이 생길 수 있다.

외부 5V 전원을 사용할 경우 전원 공급 방식을 하나로 정해야 한다. Arduino USB 5V와 외부 5V 어댑터를 같은 5V 레일에 무작정 병렬 연결하지 말고, 최소한 공통 GND만 확실히 묶은 뒤 서보/부저 전원 레일을 별도로 공급하는 구성을 우선한다.

## 1. Arduino UNO R4 WiFi

**구매 링크**: https://www.devicemart.co.kr/goods/view?no=15088648

### 역할

Arduino는 출입 허용 여부를 스스로 판단하지 않는다. 입력 장치의 원시 이벤트를 서버로 보내고, 서버가 내려준 명령만 실행한다.

| 기능 | 동작 |
|---|---|
| 부팅 보고 | `SYSTEM_READY`를 Serial로 2회 전송 |
| NFC 감지 | `WAKEUP:NFC:<UID>` 전송 |
| PIN 입력 | `WAKEUP:PW:<PIN>` 전송 |
| 성공 명령 수신 | `OPEN_DOOR` 또는 `ACTION:OPEN` 수신 시 서보 열림 |
| 실패 명령 수신 | `AUTH_FAIL` 수신 시 실패음 |
| 보안 잠금 | `LOCKDOWN` 수신 시 경고음 |

### 주요 스펙

| 항목 | 내용 |
|---|---|
| MCU | Renesas RA4M1, Arm Cortex-M4, 48MHz |
| 보조 무선 모듈 | ESP32-S3, Wi-Fi/Bluetooth 연결용 |
| Flash / SRAM | 256KB Flash, 32KB SRAM |
| 동작 로직 | GPIO 5V |
| USB | USB-C |
| 입력 전압 | USB-C 또는 VIN/barrel jack |
| 프로젝트 Baud Rate | 9600 |

### 프로젝트 주의사항

- UNO R4 WiFi의 GPIO는 5V 로직이므로 MFRC522처럼 3.3V 입력을 요구하는 모듈에는 레벨 시프터를 사용한다.
- 서보 전원은 Arduino GPIO 핀에서 공급하지 않는다.
- `Serial.begin(9600)` 이후 펌웨어가 `SYSTEM_READY`를 두 번 보내므로 서버 콘솔에서 같은 메시지가 두 번 보일 수 있다.

## 2. RFID-RC522 / MFRC522 NFC 모듈

**구매 링크**: https://www.devicemart.co.kr/goods/view?no=1279308

### 역할

13.56MHz NFC/RFID 태그의 UID를 읽어 1차 인증 수단으로 사용한다. 현재 펌웨어에서는 `NFC_ACTIVE=true`이므로 부팅 시 MFRC522 라이브러리가 초기화된다.

### 주요 스펙

| 항목 | 내용 |
|---|---|
| 칩 | MFRC522 |
| 주파수 | 13.56MHz |
| 지원 카드 | ISO/IEC 14443A 계열, MIFARE 계열 |
| 통신 | SPI |
| 전원 | 3.3V |
| 프로젝트 연결 | `D10/D11/D12/D13/D9` |

### 프로젝트 핀 연결

| MFRC522 핀 | Arduino 연결 | 레벨 시프터 | 비고 |
|---|---|---|---|
| `SDA` 또는 `SS` | `D10` | 필요 | Slave Select |
| `SCK` | `D13` | 필요 | SPI Clock |
| `MOSI` | `D11` | 필요 | Arduino -> NFC |
| `MISO` | `D12` | 현재 직결 | NFC -> Arduino, 3.3V 출력 |
| `RST` | `D9` | 필요 | Reset |
| `IRQ` | 미연결 | 없음 | 현재 코드에서 사용 안 함 |
| `GND` | 공통 GND | 없음 | 필수 |
| `3.3V` | 3.3V 레일 | 없음 | 5V 금지 |

### 주의사항

- MFRC522 전원 핀에는 3.3V만 연결한다.
- Arduino에서 NFC로 나가는 `SCK`, `MOSI`, `SS`, `RST`는 5V 신호이므로 레벨 시프터를 거친다.
- `MISO`는 MFRC522에서 Arduino로 들어오는 3.3V 신호라 현재 문서에서는 직결 기준이다. 인식이 불안정하면 남는 양방향 레벨 시프터 채널을 통해 연결하는 방식도 점검한다.

## 3. TTP229 4x4 터치 키패드 모듈

**구매 링크**: https://www.devicemart.co.kr/goods/view?no=1327405

### 역할

터치 키 입력을 PIN 문자열로 누적한 뒤, 4자리 이상 입력되면 서버로 `WAKEUP:PW:<PIN>`을 전송한다.

### 주요 스펙

| 항목 | 내용 |
|---|---|
| 터치 방식 | 정전식 터치 |
| 동작 전압 | 2.4V-5.5V |
| 보드 크기 | 49.3mm x 64.5mm |
| 프로젝트 모드 | 8키 모드 |
| 프로젝트 연결 | `SDO -> D2`, `SCL -> D3` |

### 현재 펌웨어의 키 매핑

현재 펌웨어는 8키 모드 기준으로 `key1`부터 `key8`까지를 숫자 `1`부터 `8`로 처리한다.

```text
key1 key2 key3 key4 key5 key6 key7 key8
  1    2    3    4    5    6    7    8
```

TP2 패드를 GND에 쇼트해서 16키 모드로 바꾸면 `arduino/doorlock_firmware/doorlock_firmware.ino`의 키패드 읽기 로직과 매핑도 같이 바꿔야 한다.

### 진단 코드

키패드만 따로 점검할 때는 `arduino/ttp229_test/ttp229_test.ino`를 업로드한다. 이 스케치는 16클럭을 계속 보내며 눌린 키 번호를 Serial Monitor에 출력한다.

## 4. SG-90 9g 서보모터

**구매 링크**: https://www.devicemart.co.kr/goods/view?no=1128421

### 역할

실제 전자식 스트라이크 대신 문 잠금 구조를 움직이는 프로토타입 액추에이터이다.

| 항목 | 내용 |
|---|---|
| 모델 | TowerPro 호환 SG-90 |
| 동작 전압 | 4.8V-6V |
| 토크 | 약 1.8kg/cm @ 4.8V |
| 속도 | 약 0.1초/60도 @ 4.8V |
| 프로젝트 신호 핀 | `D5` |
| 잠김 각도 | `0도` |
| 열림 각도 | `90도` |
| 자동 잠김 시간 | 3000ms |

### 배선

| 서보 선 | 연결 |
|---|---|
| 빨강 | 5V 레일 |
| 갈색 또는 검정 | GND 레일 |
| 주황 또는 노랑 | Arduino `D5` |

### 주의사항

- 서보는 순간적으로 수백 mA 이상을 요구할 수 있으므로 Arduino GPIO나 약한 USB 포트에서 직접 전원을 기대하지 않는다.
- 서보가 떨리거나 Arduino가 재부팅되면 전원 부족을 먼저 의심한다.
- 문 구조에 따라 `SERVO_LOCKED_POS`와 `SERVO_UNLOCKED_POS`는 현장에서 조정할 수 있다.

## 5. FQ-030 수동 부저

**구매 링크**: https://www.devicemart.co.kr/goods/view?no=1361187

### 역할

키 입력, 인증 성공, 인증 실패, Lockdown 상황을 소리로 구분한다. 수동 부저이므로 단순 HIGH/LOW가 아니라 `tone()`으로 주파수를 출력한다.

| 항목 | 내용 |
|---|---|
| 모델 | FQ-030 |
| 크기 | 14mm x 7mm |
| 종류 | 수동 피에조 부저 |
| 프로젝트 신호 핀 | `A2` |

### 현재 펌웨어의 소리 패턴

| 이벤트 | 동작 |
|---|---|
| 키 입력 | 3000Hz 짧은 beep |
| 시스템 준비 | 3000Hz -> 4000Hz |
| 인증 성공 | 2000Hz -> 3000Hz -> 4000Hz |
| 인증 실패 | 1000Hz -> 500Hz |
| Lockdown | 2000Hz 5회 반복 |

### 주의사항

- 현재 기준은 `BUZZER_IO_PIN=A2` 하나로 톤을 출력하고, 부저 전원은 5V 레일에서 받는다.
- 루트의 오래된 `arduino/doorlock_firmware.ino`에는 `D8`을 부저 전원 제어 핀으로 쓰던 흔적이 있으나, 현재 기준 펌웨어에는 적용하지 않는다.

## 6. ESP32-CAM + CH340 업로드 보드

**구매 링크**: https://www.devicemart.co.kr/goods/view?no=14121233

### 현재 프로젝트 내 위치

ESP32-CAM은 구매 목록에 포함되어 있지만 Arduino와 직접 배선하지 않는다. Arduino UNO R4 WiFi는 도어락 입출력용 USB-C Serial이고, ESP32-CAM은 별도 USB-C로 노트북에 연결한다.

중요: ESP32-CAM + CH340 USB-C 보드는 일반 USB 웹캠(UVC)이 아니다. USB-C만 꽂는다고 `DOORLOCK_CAMERA_URL=0`으로 잡히지 않는다. USB-C 직접 연결 시에는 `esp32cam/serial_camera/serial_camera.ino`를 ESP32-CAM에 올리고 Python 서버가 Serial JPEG 프로토콜로 프레임을 읽는다.

즉, 현재 시연 기준은 다음 셋 중 하나다.

| 방식 | 설명 |
|---|---|
| USB 카메라 | 서버 PC/Raspberry Pi에 직접 연결, `DOORLOCK_CAMERA_URL=0` |
| ESP32-CAM USB-C Serial | ESP32-CAM에 `esp32cam/serial_camera/serial_camera.ino` 업로드, `DOORLOCK_CAMERA_URL=serial:auto` 또는 `serial:/dev/ttyUSB0` |
| IP 카메라/ESP32-CAM 스트림 | ESP32-CAM을 독립 Wi-Fi 카메라로 띄우고 `DOORLOCK_CAMERA_URL`에 스트림 URL 지정 |

서버는 Arduino와 ESP32-CAM 포트를 고정 번호로 가정하지 않는다. Arduino는 최신 펌웨어의 `PING` -> `PONG:DOORLOCK_ARDUINO` 응답으로 식별하고, ESP32-CAM은 USB-Serial 후보를 스캔한 뒤 `PING` -> `PONG:READY` 응답으로 식별한다.

### 주요 스펙

| 항목 | 내용 |
|---|---|
| MCU | ESP32 |
| 무선 | Wi-Fi, Bluetooth |
| 카메라 | OV 계열 카메라 모듈, 현재 문서 기준 OV3660 사용 기록 |
| PSRAM | 보드 구성에 따라 4MB PSRAM |
| 전원 | 5V 보드 입력 |
| 업로드 | CH340 USB-C 업로드 보드 |

### 주의사항

- Arduino UNO R4 WiFi와 데이터선을 직접 연결하는 부품이 아니다.
- ESP32-CAM을 사용할 경우 Arduino 5V 레일에 부담을 주지 않도록 노트북 USB-C 또는 별도 5V 전원을 사용한다.
- ESP32-CAM과 Arduino는 둘 다 USB-C로 노트북에 연결하되 서로 데이터선을 직접 연결하지 않는다.
- CH340 드라이버가 필요한 PC가 있을 수 있다.

## 7. 2채널 TTL 레벨 시프터

**구매 링크**: https://www.devicemart.co.kr/goods/view?no=1384306

### 역할

Arduino UNO R4 WiFi의 5V 로직 신호를 MFRC522의 3.3V 로직으로 낮춘다.

| 항목 | 내용 |
|---|---|
| 채널 | 2채널 |
| 프로젝트 수량 | 2개 |
| 총 사용 채널 | 4채널 |
| HV | 5V |
| LV | 3.3V |
| 크기 | 약 16mm x 11mm |

### 사용 채널

| 채널 | HV 쪽 | LV 쪽 |
|---|---|---|
| 1 | Arduino `D13` | MFRC522 `SCK` |
| 2 | Arduino `D11` | MFRC522 `MOSI` |
| 3 | Arduino `D10` | MFRC522 `SDA/SS` |
| 4 | Arduino `D9` | MFRC522 `RST` |

### 주의사항

- 각 레벨 시프터에는 `HV`, `LV`, `GND`를 모두 연결해야 한다.
- HV만 연결하거나 LV만 연결하면 신호 변환이 동작하지 않는다.
- 두 레벨 시프터의 GND도 전체 공통 GND에 연결한다.

## 8. MB-102 830핀 브레드보드 및 점퍼선

**구매 링크**: https://www.devicemart.co.kr/goods/view?no=1322408

### 역할

시연 회로의 전원 레일과 신호선을 임시 구성하는 플랫폼이다.

| 항목 | 내용 |
|---|---|
| 모델 | MB-102 계열 830 point |
| 용도 | 5V, 3.3V, GND 분배 및 모듈 연결 |
| 주의 | 브레드보드 전원 레일이 중간에서 끊긴 제품이 있으므로 연속성 확인 필요 |

## 9. 현재 사용하지 않는 부품/회로

| 항목 | 현재 상태 | 설명 |
|---|---|---|
| 릴레이 모듈 | 현재 기준 펌웨어에서는 사용 안 함 | 이전 `doorlock.ino`는 릴레이 `A1` 기준이었으나 현재는 SG-90 서보로 대체 |
| 상태 LED | 코드 상수만 있음 | `LED_ACTIVE=false`라 기본 시연에서는 미사용 |
| 4x4 매트릭스 키패드 | 레거시 문서에 흔적 있음 | 현재 실제 부품은 TTP229 터치 키패드 |

## 10. 구매 및 근거 자료

| 부품 | 근거 |
|---|---|
| Arduino UNO R4 WiFi | `팀프로젝트_구매(요청)내역서_DIC캡스톤_브레드보드_2026_04_27.xlsx`, DeviceMart no. `15088648`, Arduino 공식 문서 |
| ESP32-CAM + CH340 | 구매 내역서, DeviceMart no. `14121233` |
| TTP229 터치 키패드 | 구매 내역서, DeviceMart no. `1327405` |
| RFID-RC522 | 구매 내역서, DeviceMart no. `1279308` |
| FQ-030 수동 부저 | 구매 내역서, DeviceMart no. `1361187` |
| SG-90 서보 | DeviceMart no. `1128421`, 현재 펌웨어 `SERVO_PIN=5` |
| 레벨 시프터 | DeviceMart no. `1384306`, 현재 NFC 배선 기준 |
| MB-102 브레드보드 | DeviceMart no. `1322408` |

## 11. 현장 점검 기준

| 점검 항목 | 통과 기준 |
|---|---|
| 전원 | 5V, 3.3V, GND 레일이 분리되어 있고 GND는 공통 |
| Serial | 서버 콘솔에서 `SYSTEM_READY` 수신 |
| TTP229 | 키 입력 시 Arduino Serial에 `[KEY]`와 길이 출력 |
| NFC | 태그 접촉 시 `WAKEUP:NFC:<UID>` 출력 |
| 부저 | 키 입력/성공/실패/Lockdown 패턴 구분 가능 |
| 서보 | `OPEN_DOOR` 수신 시 90도, 3초 뒤 0도로 복귀 |
| 서버 | 1차 인증 성공 후에만 얼굴 인증을 실행 |
| 로그 | SQLite `access_logs`에 `1ST_AUTH_SUCCESS`, `FINAL_SUCCESS`, `FINAL_FAIL`, `UNAUTHORIZED` 기록 |

이 기준을 만족하면 하드웨어 문서, 배선 문서, 테스트 시나리오가 같은 시스템을 가리키는 상태로 볼 수 있다.
