---
sidebar_position: 3
---

# Problem and Objective

## The Vulnerabilities of Single-Factor Authentication

Conventional physical access control systems heavily rely on single-factor authentication methodologies:
- **RFID/NFC Cards**: Susceptible to loss, theft, or unauthorized duplication.
- **PIN Codes**: Vulnerable to observation (shoulder surfing), sharing, and brute-force attacks.

When a single point of failure is compromised, an unauthorized entity gains complete access to the secured area. For high-security environments, this risk profile is unacceptable.

## Objectives of the 2FA System

This project aims to build an experimental prototype that mitigates these risks by implementing a strict Two-Factor Authentication (2FA) pipeline.

### 1. Mandatory Dual Verification
The system enforces that possessing a valid credential (NFC/PIN) is insufficient for access. It must be paired with immediate, localized biometric verification (Facial Recognition).

### 2. Centralized Auditing
Every access attempt, whether successful or rejected, must be logged with a precise timestamp and failure reason. This provides a clear audit trail for security monitoring.

### 3. Fail-Secure Design
The default state of the system is locked. The unlock command is exclusively transmitted to the relay controller only if all authentication stages pass explicitly. Any timeout, software exception, or hardware disconnect results in the door remaining locked.

## Project Boundaries

To accurately assess the system, it is crucial to understand the boundaries of this experimental prototype:

**What the system solves:**
- Prevents access using stolen NFC cards or leaked PINs if the unauthorized user's face is not registered.
- Provides a software-enforced logging mechanism for physical access attempts.

**What the system does NOT solve (Current Limitations):**
- **Physical Destruction**: It does not defend against physical destruction of the door or the lock mechanism itself.
- **Advanced Spoofing**: The prototype's vision AI uses 2D cameras and does not incorporate commercial-grade liveness detection.
- **Hardware Tampering**: If an attacker gains physical access to the relay wiring, they can bypass the Arduino logic by manually closing the circuit.
