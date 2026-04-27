---
sidebar_position: 1
---

# Test Plan and Results

This document outlines the standard validation procedures used to confirm the functional correctness of the 2FA Smart Door Lock System.

## Unit Testing

The Python backend utilizes the standard `unittest` framework to verify individual component logic. Tests can be executed locally via:

```bash
python3 -B -m unittest discover -s server -p 'test*.py'
```

Key unit test coverage includes:
- `test_validation.py`: Verifies UID normalization and PIN hashing.
- `test_database*.py`: Verifies concurrent write safety and WAL mode configuration.
- `test_vision_yolo.py`: Verifies embedding extraction arrays and cosine similarity logic using static mock images.

## System Integration Testing (Scenarios)

The following matrix represents the physical testing scenarios conducted on the integrated prototype.

| Test ID | Scenario | Procedure | Expected Result | Actual Status |
|---|---|---|---|---|
| INT-01 | Full Success | Present valid NFC card. Present registered face to camera. | Relay activates for 3 seconds. `SUCCESS` logged. | Pass |
| INT-02 | Invalid Primary | Present unregistered NFC card. | Reject immediately. `FAILURE_AUTH1` logged. Camera not activated. | Pass |
| INT-03 | Valid Primary, Invalid Face | Present valid NFC card. Present unregistered face to camera. | Reject. `FAILURE_AUTH2` logged. Relay inactive. | Pass |
| INT-04 | Valid Primary, No Face | Present valid NFC card. Cover camera lens. | Reject after timeout. `FAILURE_TIMEOUT` logged. Relay inactive. | Pass |
| INT-05 | Hardware Disconnect | Disconnect Arduino USB while backend running. | Backend gracefully handles `serial.SerialException` and attempts reconnection. | Pass |

*Note: For systems deployed without physical hardware (e.g., CI/CD), a `mock_arduino.py` script simulates the serial inputs to validate backend logic without requiring the physical rig.*
