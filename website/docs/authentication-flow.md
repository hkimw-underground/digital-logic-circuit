---
sidebar_position: 5
---

# Authentication Flow

The 2FA process requires the sequential completion of two separate verification stages. A failure at any point in the pipeline immediately halts the process, logs a failed attempt, and ensures the relay remains deactivated.

## Verification Pipeline

<div style={{ textAlign: 'center', margin: '2rem 0' }}>
  <svg width="800" height="450" viewBox="0 0 800 450" xmlns="http://www.w3.org/2000/svg" style={{ border: '1px solid #e2e8f0', borderRadius: '8px', backgroundColor: '#f8fafc' }}>
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#1e3a8a" />
      </marker>
      <marker id="arrow-red" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#e11d48" />
      </marker>
      <marker id="arrow-green" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#059669" />
      </marker>
    </defs>

    <rect x="50" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="100" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">User</text>

    <rect x="200" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="250" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">Arduino</text>

    <rect x="350" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="400" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">Backend</text>

    <rect x="500" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="550" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">Vision</text>

    <rect x="650" y="20" width="100" height="40" rx="4" fill="#1e3a8a" />
    <text x="700" y="45" textAnchor="middle" fill="#ffffff" fontWeight="bold">Database</text>

    <line x1="100" y1="60" x2="100" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />
    <line x1="250" y1="60" x2="250" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />
    <line x1="400" y1="60" x2="400" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />
    <line x1="550" y1="60" x2="550" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />
    <line x1="700" y1="60" x2="700" y2="430" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4" />

    <line x1="100" y1="90" x2="245" y2="90" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="175" y="80" textAnchor="middle" fill="#334155" fontSize="12">1. Tap NFC/PIN</text>

    <line x1="250" y1="110" x2="395" y2="110" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="325" y="100" textAnchor="middle" fill="#334155" fontSize="12">2. Transmit Serial</text>

    <line x1="400" y1="130" x2="695" y2="130" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="550" y="120" textAnchor="middle" fill="#334155" fontSize="12">3. Query Credential</text>

    <line x1="700" y1="150" x2="405" y2="150" stroke="#1e3a8a" strokeWidth="2" strokeDasharray="2" markerEnd="url(#arrow)" />
    <text x="550" y="145" textAnchor="middle" fill="#334155" fontSize="12">4. Valid (UID/Hash match)</text>

    <line x1="400" y1="180" x2="545" y2="180" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="475" y="170" textAnchor="middle" fill="#334155" fontSize="12">5. Req Face Auth</text>

    <line x1="550" y1="200" x2="105" y2="200" stroke="#1e3a8a" strokeWidth="2" strokeDasharray="2" markerEnd="url(#arrow)" />
    <text x="325" y="195" textAnchor="middle" fill="#334155" fontSize="12">6. Capture Frame</text>

    <line x1="550" y1="230" x2="405" y2="230" stroke="#1e3a8a" strokeWidth="2" markerEnd="url(#arrow)" />
    <text x="475" y="225" textAnchor="middle" fill="#334155" fontSize="12">7. Match Result</text>

    <rect x="90" y="250" width="620" height="70" fill="#ecfdf5" stroke="#059669" strokeWidth="1" />
    <text x="95" y="265" fill="#059669" fontWeight="bold" fontSize="12">If Match Success</text>

    <line x1="400" y1="280" x2="695" y2="280" stroke="#059669" strokeWidth="2" markerEnd="url(#arrow-green)" />
    <text x="550" y="275" textAnchor="middle" fill="#059669" fontSize="12">8a. Log EVENT_SUCCESS</text>

    <line x1="400" y1="305" x2="255" y2="305" stroke="#059669" strokeWidth="2" markerEnd="url(#arrow-green)" />
    <text x="325" y="300" textAnchor="middle" fill="#059669" fontSize="12">9a. Send UNLOCK Cmd</text>

    <rect x="90" y="330" width="620" height="70" fill="#fff1f2" stroke="#e11d48" strokeWidth="1" />
    <text x="95" y="345" fill="#e11d48" fontWeight="bold" fontSize="12">If Match Failed</text>

    <line x1="400" y1="360" x2="695" y2="360" stroke="#e11d48" strokeWidth="2" markerEnd="url(#arrow-red)" />
    <text x="550" y="355" textAnchor="middle" fill="#e11d48" fontSize="12">8b. Log FAILURE_AUTH2</text>

    <line x1="400" y1="385" x2="255" y2="385" stroke="#e11d48" strokeWidth="2" markerEnd="url(#arrow-red)" />
    <text x="325" y="380" textAnchor="middle" fill="#e11d48" fontSize="12">9b. Send DENY Cmd</text>

  </svg>
</div>

## Failure Handling Policies

The system is designed to be **fail-secure**.

1. **NFC / PIN Failure:**
   - If the NFC UID is not registered, or the PIN hash does not match, the system logs a `PRIMARY_AUTH_FAILED` event. The vision module is not invoked.
2. **Face Verification Failure:**
   - If a valid primary credential is provided but the camera detects no face, detects multiple faces (ambiguity), or the face does not match the registered profile for the given UID, the system logs a `SECONDARY_AUTH_FAILED` event.
3. **Hardware / Timeout Failure:**
   - If the backend loses connection with the Arduino, or the vision module times out, the backend handles the exception and logs a `SYSTEM_ERROR`. The Arduino requires an explicit positive command to unlock; without it, the relay remains locked.
