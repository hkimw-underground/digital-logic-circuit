---
sidebar_position: 1
---

# Hardware Overview

This section details the physical components utilized in the 2FA prototype.

### Core Components

1. **Microcontroller (Arduino Uno/Nano)**
   - Acts as the peripheral manager. Reads localized sensor data and toggles output pins based on serial instructions.
2. **RFID/NFC Reader (MFRC522)**
   - Communicates via SPI protocol to read the UID of 13.56MHz cards/tags.
3. **4x4 Matrix Keypad**
   - Provides alternative primary authentication via PIN entry.
4. **Relay Module**
   - Acts as an electrically operated switch to control high-current circuits (e.g., electronic door strikes or magnetic locks).

### Limitations and Safety Warnings

When implementing this hardware prototype, several critical engineering constraints must be observed:

- **Logic Levels (3.3V vs 5V):** The MFRC522 module operates strictly on 3.3V logic. Connecting its logic pins directly to a 5V Arduino without level shifting can damage the module or cause unreliable reads. Ensure proper logic level conversion.
- **Power Isolation:** An electronic lock (solenoid/maglock) draws significant current and produces inductive kickback. **Never power the lock directly from the Arduino's 5V or Vin pins.** The lock must have an independent, appropriately rated power supply. The relay should provide complete optical and galvanic isolation between the Arduino and the lock circuit.
- **Fail-Secure vs. Fail-Safe:** Depending on the physical lock mechanism chosen, the system behavior during a total power failure will vary. The prototype assumes a standard electronic strike (fail-secure), which remains locked when power is lost.
