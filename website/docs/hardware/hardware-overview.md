---
sidebar_position: 1
---

# 하드웨어 개요

본 섹션은 현재 시연 기준의 2FA 스마트 도어락 하드웨어 구성을 설명한다. 기준 펌웨어는 `arduino/doorlock_firmware/doorlock_firmware.ino`이며, 보드는 Arduino UNO R4 WiFi이다.

## 하드웨어 구성 요소

### 1. 제어 모듈

- **Arduino UNO R4 WiFi**
  - TTP229 키패드와 MFRC522 NFC 입력을 읽는다.
  - Python 서버와 USB Serial 9600 baud로 통신한다.
  - 서버가 보낸 `OPEN_DOOR`, `AUTH_FAIL`, `LOCKDOWN` 명령에 따라 서보와 부저를 제어한다.

### 2. 입력 모듈

- **MFRC522 NFC 리더**
  - 13.56MHz 태그 UID를 읽어 1차 인증 수단으로 사용한다.
  - SPI 핀은 `D10/D11/D12/D13`, Reset은 `D9`를 사용한다.
  - 모듈 전원은 3.3V이며, Arduino에서 NFC로 나가는 5V 신호는 레벨 시프터를 거친다.

- **TTP229 터치 키패드**
  - 현재 펌웨어는 8키 모드 기준이다.
  - `SDO -> D2`, `SCL -> D3`로 연결한다.
  - 4자리 이상 입력되면 `WAKEUP:PW:<PIN>` 형식으로 서버에 전달한다.

- **카메라**
  - Python 서버가 OpenCV로 읽는 USB 카메라, IP 카메라, 또는 ESP32-CAM USB-Serial JPEG 소스를 사용한다.
  - ESP32-CAM은 Arduino에 직접 배선하지 않고 노트북에 별도 USB-C로 연결한다.
  - ESP32-CAM + CH340 보드는 일반 USB 웹캠이 아니므로 `esp32cam/serial_camera/serial_camera.ino`를 업로드한 뒤 `DOORLOCK_CAMERA_URL=serial:auto`로 읽는다.

### 3. 출력 모듈

- **SG-90 서보모터**
  - 현재 시연용 잠금/해제 액추에이터이다.
  - 신호선은 `D5`, 잠김 각도는 `0도`, 열림 각도는 `90도`이다.
  - `OPEN_DOOR` 수신 후 약 3초 뒤 자동으로 잠김 각도로 복귀한다.

- **FQ-030 수동 부저**
  - 신호선은 `A2`이다.
  - 키 입력, 인증 성공, 인증 실패, Lockdown 상태를 서로 다른 `tone()` 패턴으로 알린다.

## 구현 시 주의사항

- **전압 레벨:** MFRC522에는 3.3V만 공급한다. `SCK`, `MOSI`, `SS`, `RST`는 레벨 시프터를 거친다.
- **공통 GND:** Arduino, 키패드, NFC, 서보, 부저, 외부 전원은 GND 기준을 공유해야 한다.
- **서보 전원:** 서보는 순간 전류가 크므로 전원 부족 시 떨림이나 Arduino 재부팅이 발생할 수 있다.
- **외부 전원:** 외부 5V 어댑터를 쓸 때 Arduino USB 5V와 같은 레일에 병렬로 묶지 않는다. 서보/부저 전원만 별도 공급하고 GND를 공통으로 묶는 구성을 우선한다.
- **레거시 스케치:** `arduino/doorlock.ino`와 루트의 `arduino/doorlock_firmware.ino`는 현재 배선 기준이 아니다.
