---
sidebar_position: 4
---

# System Architecture

The 2FA Smart Door Lock System is composed of several interdependent modules spanning hardware, backend logic, data persistence, and computer vision.

## Architecture Overview

*Note: For a detailed SVG visualization, please refer to the customized architecture diagram below.*

<div style={{ textAlign: 'center', margin: '2rem 0' }}>
  <svg width="800" height="400" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" style={{ border: '1px solid #e2e8f0', borderRadius: '8px', backgroundColor: '#f8fafc' }}>
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#1e3a8a" />
      </marker>
    </defs>

    {/* Client Layer */}
    <rect x="50" y="50" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="125" y="85" textAnchor="middle" fill="#0f172a" fontWeight="bold">Hardware Inputs</text>
    <text x="125" y="105" textAnchor="middle" fill="#334155" fontSize="12">NFC Reader &amp; Keypad</text>

    {/* Arduino */}
    <rect x="50" y="180" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="125" y="215" textAnchor="middle" fill="#0f172a" fontWeight="bold">Microcontroller</text>
    <text x="125" y="235" textAnchor="middle" fill="#334155" fontSize="12">Arduino (Serial)</text>

    {/* Lock */}
    <rect x="50" y="300" width="150" height="50" rx="8" fill="#ffffff" stroke="#e11d48" strokeWidth="2" />
    <text x="125" y="330" textAnchor="middle" fill="#0f172a" fontWeight="bold">Relay / Door Lock</text>

    {/* Backend Layer */}
    <rect x="325" y="180" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="400" y="215" textAnchor="middle" fill="#0f172a" fontWeight="bold">Backend Server</text>
    <text x="400" y="235" textAnchor="middle" fill="#334155" fontSize="12">Python FastAPI</text>

    {/* Vision Layer */}
    <rect x="600" y="50" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="675" y="85" textAnchor="middle" fill="#0f172a" fontWeight="bold">Vision Module</text>
    <text x="675" y="105" textAnchor="middle" fill="#334155" fontSize="12">YOLOv8 / OpenCV</text>

    {/* DB Layer */}
    <rect x="600" y="180" width="150" height="80" rx="8" fill="#ffffff" stroke="#1e3a8a" strokeWidth="2" />
    <text x="675" y="215" textAnchor="middle" fill="#0f172a" fontWeight="bold">Database</text>
    <text x="675" y="235" textAnchor="middle" fill="#334155" fontSize="12">SQLite</text>

    {/* Web Dashboard */}
    <rect x="600" y="300" width="150" height="50" rx="8" fill="#ffffff" stroke="#059669" strokeWidth="2" />
    <text x="675" y="330" textAnchor="middle" fill="#0f172a" fontWeight="bold">Web Dashboard</text>

    {/* Connections */}
    <path d="M 125 130 L 125 180" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 125 260 L 125 300" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 200 220 L 325 220" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 325 200 L 200 200" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />

    <path d="M 400 180 L 400 90 L 600 90" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 475 220 L 600 220" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />
    <path d="M 400 260 L 400 325 L 600 325" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#arrow)" />

  </svg>
</div>

## Component Responsibilities

| Module | Responsibility | Technology |
|---|---|---|
| **Microcontroller** | Polls NFC and Keypad hardware, transmits raw inputs over Serial, and toggles the relay based strictly on server commands. | Arduino Uno/Nano, C++ |
| **Backend API** | Orchestrates authentication logic. Verifies primary credentials, invokes the vision module, sends serial commands, and handles event persistence. | Python, FastAPI, PySerial |
| **Vision Module** | Captures camera frames, detects faces, and compares the detected face against registered profiles for secondary authentication. | OpenCV, YOLOv8 |
| **Database** | Securely stores user credentials (hashed PINs, NFC UIDs) and immutable access logs. | SQLite |
| **Web Frontend** | Displays a validation summary and system health metrics for monitoring purposes. | React, Docusaurus |

## Data vs Control Flow

**Data Flow:**
1. Raw hardware inputs (UID, Keystrokes) flow from the Arduino to the Backend.
2. Camera frames are processed entirely within the Vision Module on the server side.
3. Authentication results flow from the Backend to the Database as log entries.

**Control Flow:**
1. The Backend is the sole authority for access decisions.
2. If the Backend determines access is granted, it sends an explicit `UNLOCK` serial command to the Arduino.
3. The Arduino executes the physical relay switch. It does not possess any autonomous decision-making capability regarding access rights.

## Data Flow Diagram

<div style={{ textAlign: 'center', margin: '2rem 0' }}>
  <svg width="700" height="200" viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" style={{ border: '1px solid #e2e8f0', borderRadius: '8px', backgroundColor: '#f8fafc' }}>
    <defs>
      <marker id="df-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#1e3a8a" />
      </marker>
    </defs>

    <rect x="50" y="80" width="100" height="40" rx="8" fill="#e2e8f0" stroke="#1e3a8a" strokeWidth="1" />
    <text x="100" y="105" textAnchor="middle" fill="#0f172a" fontSize="12">Hardware</text>

    <rect x="300" y="80" width="100" height="40" rx="8" fill="#1e3a8a" />
    <text x="350" y="105" textAnchor="middle" fill="#ffffff" fontSize="12">FastAPI Backend</text>

    <rect x="550" y="80" width="100" height="40" rx="8" fill="#e2e8f0" stroke="#1e3a8a" strokeWidth="1" />
    <text x="600" y="105" textAnchor="middle" fill="#0f172a" fontSize="12">SQLite Log</text>

    {/* Forward flow */}
    <path d="M 150 90 L 300 90" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#df-arrow)" />
    <text x="225" y="80" textAnchor="middle" fill="#334155" fontSize="10">UID/PIN Input</text>

    {/* Return flow */}
    <path d="M 300 110 L 150 110" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#df-arrow)" />
    <text x="225" y="125" textAnchor="middle" fill="#334155" fontSize="10">UNLOCK Command</text>

    {/* Log flow */}
    <path d="M 400 100 L 550 100" stroke="#1e3a8a" strokeWidth="2" fill="none" markerEnd="url(#df-arrow)" />
    <text x="475" y="90" textAnchor="middle" fill="#334155" fontSize="10">Log Persistence</text>
  </svg>
</div>
