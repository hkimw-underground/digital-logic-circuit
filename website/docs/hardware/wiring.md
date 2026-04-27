---
sidebar_position: 2
---

# Wiring and Pin Mapping

The following pin mappings are derived from the project's source configuration (`doorlock.ino`).

### Hardware Connection Diagram

<div style={{ textAlign: 'center', margin: '2rem 0' }}>
  <svg width="700" height="400" viewBox="0 0 700 400" xmlns="http://www.w3.org/2000/svg" style={{ border: '1px solid #e2e8f0', borderRadius: '8px', backgroundColor: '#f8fafc' }}>
    <rect x="250" y="150" width="200" height="100" rx="8" fill="#1e3a8a" />
    <text x="350" y="205" textAnchor="middle" fill="#ffffff" fontWeight="bold">Arduino Uno/Nano</text>

    <rect x="50" y="50" width="120" height="60" rx="4" fill="#0f172a" />
    <text x="110" y="85" textAnchor="middle" fill="#ffffff" fontSize="14">MFRC522</text>

    <rect x="50" y="280" width="120" height="60" rx="4" fill="#0f172a" />
    <text x="110" y="315" textAnchor="middle" fill="#ffffff" fontSize="14">4x4 Keypad</text>

    <rect x="530" y="100" width="120" height="60" rx="4" fill="#e11d48" />
    <text x="590" y="135" textAnchor="middle" fill="#ffffff" fontSize="14">Relay</text>

    <rect x="530" y="250" width="120" height="60" rx="4" fill="#334155" />
    <text x="590" y="285" textAnchor="middle" fill="#ffffff" fontSize="14">Door Lock</text>

    {/* MFRC522 Lines */}
    <path d="M 170 80 C 250 80, 300 150, 300 150" stroke="#3b82f6" strokeWidth="2" fill="none" />
    <text x="210" y="70" fill="#334155" fontSize="12">SPI (10, 11, 12, 13)</text>

    {/* Keypad Lines */}
    <path d="M 170 310 C 250 310, 300 250, 300 250" stroke="#3b82f6" strokeWidth="2" fill="none" />
    <text x="210" y="325" fill="#334155" fontSize="12">D2-D8, A0</text>

    {/* Relay Lines */}
    <path d="M 450 170 L 530 130" stroke="#ef4444" strokeWidth="2" fill="none" />
    <text x="490" y="140" fill="#ef4444" fontSize="12">A1</text>

    {/* Lock Line */}
    <path d="M 590 160 L 590 250" stroke="#e11d48" strokeWidth="2" fill="none" strokeDasharray="4" />
    <text x="600" y="210" fill="#334155" fontSize="12">12V Switched</text>
  </svg>
</div>

### MFRC522 (SPI Interface)

| MFRC522 Pin | Arduino Pin | Notes |
|---|---|---|
| SDA (SS) | 10 | Slave Select |
| SCK | 13 | Serial Clock |
| MOSI | 11 | Master Out Slave In |
| MISO | 12 | Master In Slave Out |
| IRQ | Not Connected | |
| GND | GND | Common Ground |
| RST | A2 | Reset |
| 3.3V | 3.3V | **Do not connect to 5V** |

### 4x4 Matrix Keypad

| Keypad Row/Col | Arduino Pin |
|---|---|
| Row 1 | 2 |
| Row 2 | 3 |
| Row 3 | 4 |
| Row 4 | 5 |
| Col 1 | 6 |
| Col 2 | 7 |
| Col 3 | 8 |
| Col 4 | A0 |

### Relay Module

| Relay Pin | Arduino Pin | Notes |
|---|---|---|
| VCC | 5V | |
| GND | GND | Common Ground |
| IN | A1 | Control Signal (Active Low/High depending on module) |

*Assumption:* The Arduino logic assumes `RELAY_LOCKED = LOW` and `RELAY_UNLOCKED = HIGH`. This can be adjusted in the firmware based on the specific relay hardware used.
