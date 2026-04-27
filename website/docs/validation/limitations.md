---
sidebar_position: 2
---

# Limitations

The current implementation of the 2FA Smart Door Lock System is an experimental prototype. It successfully demonstrates the integration of multiple hardware sensors and computer vision logic, but it possesses several limitations that preclude its use in production environments.

### 1. Cryptographic Security of Serial Links
The communication between the Backend Server and the Microcontroller is transmitted as plaintext over USB Serial. An attacker with physical access to the cabling can trivially inject an `UNLOCK` string to bypass all software authentication. Production systems require encrypted data buses (e.g., OSDP protocol).

### 2. Biometric Anti-Spoofing
The vision module utilizes standard 2D webcams. It is vulnerable to presentation attacks using high-resolution photographs or video playback. Commercial systems mitigate this utilizing depth sensors (stereo cameras, IR structured light).

### 3. Relay Isolation and Physical Security
The prototype does not enforce physical isolation of the relay. If the relay module is exposed, the lock can be actuated by manually bridging the output terminals. Robust enclosures and secure-side mounting of critical switching hardware are required.

### 4. Limited User Administration
Currently, user registration is handled via direct backend API calls or basic web endpoints. The system lacks a comprehensive Identity and Access Management (IAM) interface for bulk enrollment, role-based access control, or scheduled access policies.

### 5. Single Node Architecture
The SQLite database and vision processing occur on a single local node. There is no synchronization with a centralized server, meaning multi-door deployments would operate as entirely independent silos.
