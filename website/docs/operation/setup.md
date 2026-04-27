---
sidebar_position: 1
---

# System Setup and Deployment

This document outlines the standard procedures for configuring, building, and deploying both the hardware prototype and the accompanying software infrastructure of the 2FA Smart Door Lock System.

## Repository Structure

The project is structured into three primary domains:
- `/arduino`: Contains the C++ firmware (`doorlock.ino`) for the microcontroller.
- `/server`: Contains the Python FastAPI backend, SQLite database logic, and OpenCV/YOLOv8 vision modules.
- `/website`: Contains the Docusaurus-based technical documentation and React frontend dashboard.

## Local Development Prerequisites

- **Hardware**: Arduino Uno/Nano, MFRC522 RFID module, 4x4 Matrix Keypad, 5V/12V Relay module.
- **Software**: Node.js (v20+), Python 3.10+, Arduino IDE.

### Hardware Limitations and Safety Warnings

Before physical assembly, adhere to the following engineering constraints:
- **Logic Levels**: The MFRC522 operates strictly on 3.3V logic. Directly connecting its logic pins to a 5V Arduino without proper level shifting may damage the module.
- **Power Isolation**: The Arduino GPIO pins **must not directly power** a high-current load such as a door lock or solenoid.
- **Relay Configuration**: The lock must have an independent, appropriately rated power supply. The relay provides optical/galvanic isolation between the Arduino logic circuit and the high-current lock circuit.
- **Scope**: This prototype is an experimental implementation and is **not** a certified commercial access-control product.

## Software Setup Commands

### Documentation Website

The technical report and dashboard are built using Docusaurus.

```bash
cd website
npm install
npm run build
```

### Backend Server

The backend utilizes Python and FastAPI. In restricted environments where new `pip` dependencies cannot be installed, rely on the standard library testing framework.

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server
python3 server/main.py
```

### Testing

The system employs `unittest` for backend validation.

```bash
source .venv/bin/activate
python3 -B -m unittest discover -s server -p 'test*.py'
```

## Mock Execution (CI/Cloud Environments)

In cloud environments, CI/CD pipelines, or autonomous workspaces (e.g., Jules) where physical hardware (Arduino, camera, relay) is unavailable, the system supports a simulated execution mode.

- **Vision AI Mocking**: Set the environment variable `DOORLOCK_VISION_MOCK=1` to bypass physical webcam frame capture and rely on static test assertions.
- **Hardware Mocking**: Execute `python3 server/mock_arduino.py` to manually simulate serial events (e.g., NFC taps, PIN inputs) and observe the backend's relay logic without a physical Arduino connected.

*Note: While mock mode validates software logic, real hardware behavior (timing, voltage drops, serial noise) must be validated separately on the physical rig.*

## GitHub Pages Deployment

The documentation site is configured for static hosting via GitHub Pages.
- **Build Source**: The site is built from the `/website` directory.
- **Base URL**: Configured as `/digital-logic-circuit/` in `docusaurus.config.js`.
- **Public URL**: [https://school-project-hwkim-dev.github.io/digital-logic-circuit/](https://school-project-hwkim-dev.github.io/digital-logic-circuit/)

## Build Validation Checklist

Prior to committing changes to the `main` branch, ensure the following criteria are met:
- [ ] `npm run build` succeeds without fatal errors.
- [ ] No broken internal or external Docusaurus links exist.
- [ ] Diagram components render correctly (no raw code blocks visible).
- [ ] No "Mock", "Placeholder", or "TODO" text remains visible in the final public UI.
