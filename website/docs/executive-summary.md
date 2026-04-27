---
sidebar_position: 2
---

# Executive Summary

### Project Purpose
The purpose of this project is to develop and evaluate an experimental prototype of a Two-Factor Authentication (2FA) Smart Door Lock System. The system addresses the inherent risks of single-factor access control by requiring two distinct forms of identification prior to granting physical access.

### System Configuration
The system integrates a micro-controller (Arduino Uno/Nano) with a centralized Python backend.
- **Hardware Controller**: The Arduino manages localized inputs (MFRC522 NFC reader, 4x4 matrix keypad) and controls the unlocking mechanism via a relay module.
- **Backend Infrastructure**: A FastAPI-based server orchestrates the authentication logic, interfaces with an SQLite database for credential storage and event logging, and utilizes YOLOv8/OpenCV for the secondary facial verification stage.

### Validation Results
Basic functional testing confirms the operational sequence:
1. The backend accurately validates NFC UIDs and PIN inputs.
2. Upon primary success, the vision module evaluates the user's face.
3. The relay is energized to unlock the door only when both stages pass.
4. Access failures at any stage immediately terminate the sequence and are logged to the database.

*See the Validation section for detailed statistics and test plans.*

### Key Risks and Limitations
While the system successfully demonstrates a 2FA workflow, several limitations exist within the current prototype:
- **Hardware Isolation**: The relay-controlled lock requires a separate, isolated power source. Direct integration with high-voltage or critical infrastructure was not performed.
- **Physical Bypass**: The system is vulnerable to physical relay bypass attacks. Software enforcement cannot prevent direct physical tampering with the relay wiring.
- **Spoofing Vulnerability**: The facial recognition module, relying on standard RGB camera input, remains susceptible to high-quality 2D spoofing (e.g., printed photographs or high-resolution digital displays).
- **Serial Communication**: Command transmission between the backend server and the Arduino currently utilizes unencrypted serial communication.

### Future Improvements
Future iterations should address the identified limitations by:
1. Implementing encrypted serial communication protocols.
2. Upgrading to a depth-sensing camera (e.g., IR or stereo vision) for robust anti-spoofing.
3. Enclosing hardware components in a tamper-resistant housing.
