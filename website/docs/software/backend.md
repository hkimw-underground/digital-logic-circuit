---
sidebar_position: 1
---

# Backend Architecture

The backend serves as the authoritative decision-making component of the system. It processes incoming data from the Arduino, interfaces with the vision module, and maintains the database.

## Core Modules

1. **`main.py` / `app.py`:**
   - Initializes the FastAPI web application.
   - Manages API routing for web dashboards and external integrations.
2. **`serial_manager.py`:**
   - Handles asynchronous serial communication with the Arduino.
   - Parses incoming UID/PIN strings and dispatches them to the validation logic.
   - Provides a `mock` mode for CI/CD environments where physical hardware is absent.
3. **`vision_ai.py`:**
   - Manages the YOLOv8 and OpenCV pipeline.
   - Captures frames from the connected camera.
   - Extracts facial embeddings and performs cosine similarity matching against registered profiles.
4. **`validation.py`:**
   - Orchestrates the two-stage authentication logic.
   - Ensures UID formatting consistency.

## API Endpoints (Web Interface)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/logs` | GET | Retrieve a paginated list of access logs. |
| `/api/status` | GET | Retrieve system health metrics (DB connection, Vision module status). |
| `/api/register` | POST | Register a new user with NFC UID and initial facial scan. |

*Note: Administrative endpoints require separate network-level authentication, which is outside the scope of this hardware prototype documentation.*
