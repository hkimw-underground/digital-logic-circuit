---
sidebar_position: 2
---

# User Guide and Operation

This document details the standard operating procedures and expected behavior of the 2FA Smart Door Lock System from an end-user and administrator perspective.

## System Startup Sequence

1. **Power Initialization**: Ensure the Arduino and the independent lock power supply are energized.
2. **Backend Initialization**: Start the Python FastAPI server (`server/main.py`). The server will automatically initialize the SQLite database if it does not exist.
3. **Serial Handshake**: Upon startup, the Arduino broadcasts a `SYSTEM_READY` signal over the USB serial connection. The backend acknowledges this signal and begins the polling loop.
4. **Vision Module Warm-up**: The YOLOv8 model is loaded into memory. The system is fully operational once the backend logs indicate the camera feed is successfully captured.

## Authentication Flow (End-User)

To gain access, a registered user must successfully complete the two-factor authentication pipeline.

### Step 1: Primary Authentication (NFC or PIN)
The user initiates the process by presenting a registered credential to the localized hardware.
- **NFC Method**: Tap a registered 13.56MHz card against the MFRC522 reader.
- **PIN Method**: Input a registered 4-digit code using the matrix keypad, followed by the specific termination key (e.g., `#` or `A`, depending on configuration).

*If the primary credential is valid, the system immediately proceeds to Step 2.*

### Step 2: Secondary Authentication (Facial Verification)
Upon primary success, the backend activates the vision module.
- The user must stand within the camera's field of view.
- The system captures a frame, extracts facial embeddings via YOLOv8, and compares them against the stored profile associated with the primary credential.

### Step 3: Relay Unlock Behavior
- If the facial verification returns a positive match, the backend transmits an explicit `UNLOCK` command via serial.
- The Arduino toggles the relay pin, energizing the lock mechanism for a pre-configured duration (default: 3000ms), allowing physical entry.
- The system immediately relocks after the timeout expires.

## Failure Handling and Logging

The system is designed to default to a secure, locked state upon any failure. All authentication attempts are immutably logged to the SQLite `access_logs` table.

- **Primary Failure**: If an unregistered NFC card is tapped or an incorrect PIN is entered, the event is logged as `FAILURE_AUTH1`. The vision module is not engaged.
- **Secondary Failure**: If the primary credential is valid but the camera detects a mismatched face, multiple faces, or no face within the timeout period, the event is logged as `FAILURE_AUTH2`. The door remains locked.
- **Hardware Disconnect**: If the serial connection to the Arduino is severed, the backend logs a critical system error. The Arduino, lacking an `UNLOCK` command, will keep the relay disengaged.

## Dashboard Monitoring

Administrators can monitor the system's performance and audit access logs via the web dashboard.
- Navigate to the **Validation Status** page on the deployed Docusaurus site.
- The dashboard provides a summary of total authentication attempts, success/failure ratios, and a distribution of failure reasons based on the static validation dataset.

## Manual Validation (Mock Mode)

For development or demonstration purposes without physical hardware:
1. Ensure the backend is running.
2. Execute `python3 server/mock_arduino.py` in a separate terminal.
3. Use the CLI prompts to inject simulated NFC UIDs or PIN codes.
4. Observe the backend logs to verify the two-stage logic and the correct transmission of the simulated `UNLOCK` command.

## Known Operational Limitations

- **Lighting Dependency**: The facial verification module utilizes standard RGB webcams and its accuracy is degraded in low-light environments.
- **Single Node Logging**: Audit logs are stored locally on the host machine running the Python backend. Multi-door synchronization is not currently supported.
