---
sidebar_position: 2
---

# Database Schema

The system uses an embedded SQLite database (`database.py`) to ensure local, zero-network-dependency operation. The database operates in WAL (Write-Ahead Logging) mode to support concurrent reads from the web dashboard while the authentication loop writes logs.

## Tables

### 1. `users`

Stores registered user credentials.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | Unique internal identifier. |
| `name` | TEXT | NOT NULL | Display name. |
| `nfc_uid` | TEXT | UNIQUE | Normalized NFC card UID. |
| `pin_hash` | TEXT | | Bcrypt hashed PIN code (optional). |
| `face_encoding` | BLOB | | Serialized vector array of the user's face. |

### 2. `access_logs`

Provides an immutable audit trail of all system activity.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY | Unique log entry ID. |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Time of the event. |
| `nfc_uid` | TEXT | | The UID presented (if any). |
| `status` | TEXT | NOT NULL | E.g., `SUCCESS`, `FAILURE_AUTH1`, `FAILURE_AUTH2`. |
| `reason` | TEXT | | Detailed failure context (e.g., "Face Mismatch"). |
