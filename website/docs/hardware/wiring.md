---
sidebar_position: 2
---

# 배선 및 핀 맵 (Wiring and Pin Mapping)

본 섹션은 프로젝트의 소스 코드(`doorlock.ino`)에 정의된 하드웨어 연결 구성과 핀 맵을 설명한다. 모든 연결은 Arduino Uno/Nano 호환 보드를 기준으로 설계되었다.

### 하드웨어 연결 다이어그램

<div style={{ textAlign: 'center', margin: '2rem 0' }}>
  <svg width="700" height="400" viewBox="0 0 700 400" xmlns="http://www.w3.org/2000/svg" style={{ border: '1px solid #e2e8f0', borderRadius: '8px', backgroundColor: '#f8fafc' }}>
    {/* 중앙 컨트롤러 */}
    <rect x="250" y="150" width="200" height="100" rx="8" fill="#1e3a8a" />
    <text x="350" y="205" textAnchor="middle" fill="#ffffff" fontWeight="bold" fontSize="18">Arduino Uno/Nano</text>

    {/* 입력 장치 */}
    <rect x="50" y="50" width="140" height="70" rx="4" fill="#334155" />
    <text x="120" y="90" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="bold">MFRC522 (NFC)</text>

    <rect x="50" y="280" width="140" height="70" rx="4" fill="#334155" />
    <text x="120" y="320" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="bold">4x4 Keypad</text>

    {/* 출력 및 액추에이터 */}
    <rect x="510" y="100" width="140" height="70" rx="4" fill="#1e3a8a" />
    <text x="580" y="140" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="bold">Relay Module</text>

    <rect x="510" y="250" width="140" height="70" rx="4" fill="#64748b" />
    <text x="580" y="290" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="bold">Electronic Lock</text>

    {/* 배선 연결선 */}
    {/* MFRC522 to Arduino */}
    <path d="M 190 85 Q 350 85, 350 150" stroke="#1e3a8a" strokeWidth="2" fill="none" />
    <text x="210" y="80" fill="#1e3a8a" fontSize="11" fontWeight="bold">SPI: D10, D11, D12, D13, A2</text>

    {/* Keypad to Arduino */}
    <path d="M 190 315 Q 350 315, 350 250" stroke="#1e3a8a" strokeWidth="2" fill="none" />
    <text x="210" y="335" fill="#1e3a8a" fontSize="11" fontWeight="bold">GPIO: D2-D8, A0</text>

    {/* Arduino to Relay */}
    <path d="M 450 200 Q 580 200, 580 170" stroke="#1e3a8a" strokeWidth="2" fill="none" />
    <text x="470" y="190" fill="#1e3a8a" fontSize="11" fontWeight="bold">Signal: A1</text>

    {/* Relay to Lock (High Power Path) */}
    <path d="M 580 170 L 580 250" stroke="#dc2626" strokeWidth="2" fill="none" strokeDasharray="5,5" />
    <text x="590" y="215" fill="#dc2626" fontSize="11" fontWeight="bold">12V External Power</text>

    {/* 하단 캡션 */}
    <text x="350" y="380" textAnchor="middle" fill="#64748b" fontSize="12">시스템 하드웨어 인터페이스 구성도 (Hardware Interface Diagram)</text>
  </svg>
</div>

### MFRC522 (SPI 인터페이스)

NFC 리더기는 SPI 통신을 사용하여 Arduino와 데이터를 주고받는다.

| MFRC522 핀 | Arduino 핀 | 비고 |
|---|---|---|
| SDA (SS) | 10 | Slave Select |
| SCK | 13 | Serial Clock |
| MOSI | 11 | Master Out Slave In |
| MISO | 12 | Master In Slave Out |
| IRQ | 연결 안 함 | Interrupt Request (사용 안 함) |
| GND | GND | 공통 접지 (Common Ground) |
| RST | A2 | 리셋 (Reset) |
| 3.3V | 3.3V | **주의: 5V에 연결 시 모듈이 손상될 수 있음** |

### 4x4 매트릭스 키패드 (4x4 Matrix Keypad)

키패드는 8개의 GPIO 핀을 사용하여 행(Row)과 열(Col)의 교차점을 스캔한다.

| 키패드 Pin | Arduino 핀 | 역할 |
|---|---|---|
| Row 1 | 2 | 행 제어 |
| Row 2 | 3 | 행 제어 |
| Row 3 | 4 | 행 제어 |
| Row 4 | 5 | 행 제어 |
| Col 1 | 6 | 열 제어 |
| Col 2 | 7 | 열 제어 |
| Col 3 | 8 | 열 제어 |
| Col 4 | A0 | 열 제어 |

### 릴레이 모듈 (Relay Module)

릴레이는 Arduino의 저전력 신호로 도어락의 고전력 회로를 제어한다.

| 릴레이 핀 | Arduino 핀 | 비고 |
|---|---|---|
| VCC | 5V | Arduino 5V 출력 사용 가능 |
| GND | GND | 공통 접지 |
| IN | A1 | 제어 신호 (펌웨어에서 설정 가능) |

---

### 전원 설계 및 안전 주의사항

성공적인 하드웨어 구현을 위해 다음과 같은 전원 설계 원칙을 준수해야 한다.

1. **전원 분리 (Power Isolation):**
   - 전자식 도어락(솔레노이드 또는 마그네틱 락)은 작동 시 높은 전류를 소모하며, 코일의 자기장 변화로 인해 역기전력을 발생시킨다.
   - **절대로 도어락의 전원을 Arduino의 5V 또는 Vin 핀에서 직접 공급받지 않아야 한다.**
   - 도어락을 위한 별도의 12V 외부 전원 공급 장치를 사용하고, 릴레이를 통해 Arduino 제어 회로와 물리적으로 분리하여 시스템 안정성을 확보한다.

2. **논리 레벨 (Logic Levels):**
   - MFRC522 모듈은 3.3V 로직으로 동작하도록 설계되어 있다. Arduino Uno/Nano의 5V 핀에 직접 연결할 경우 즉각적인 손상이나 불안정한 동작을 유발할 수 있으므로 반드시 3.3V 전원을 사용해야 한다.

3. **릴레이 로직 설정:**
   - 본 프로젝트의 기본 펌웨어는 `RELAY_LOCKED = LOW`, `RELAY_UNLOCKED = HIGH`로 가정한다. 만약 사용하는 릴레이 모듈이 Active Low(신호가 낮을 때 동작) 방식인 경우, `doorlock.ino`의 상수를 수정하여 대응한다.
