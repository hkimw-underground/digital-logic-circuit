---
sidebar_position: 3
---

# Serial Protocol

Communication between the Arduino and the Backend Server utilizes a simple plaintext serial protocol over USB (9600 Baud).

## Message Formats

### Arduino → Server

| Event | String Format | Example |
|---|---|---|
| System Ready | `SYSTEM_READY` | `SYSTEM_READY` |
| NFC Card Tap | `UID:<hex_string>` | `UID:A1B2C3D4` |
| PIN Entry | `PIN:<string>` | `PIN:1234` |

### Server → Arduino

| Command | Action |
|---|---|
| `UNLOCK` | Instructs the Arduino to pull the relay pin HIGH/LOW for the configured unlock duration (e.g., 3000ms). |
| `DENY` | Explicit rejection command. Triggers an error beep or LED blink (if implemented). Relay state remains locked. |

*Security Note: This protocol is currently unencrypted. See the Security section regarding physical access limitations.*
