---
sidebar_position: 1
---

# Introduction

## 2FA Smart Door Lock System

This document serves as the technical report for the experimental **2-Factor Authentication (2FA) Smart Door Lock System**. It provides a comprehensive overview of the system's architecture, hardware implementation, software design, security threat model, and validation results.

### Problem Statement

Traditional single-factor authentication door lock systems, such as those relying exclusively on NFC cards or PIN codes, are vulnerable to physical theft, unauthorized sharing, and brute-force attacks. If an unauthorized individual obtains a registered NFC card, they gain unrestricted access.

### Objective and Scope

The primary objective of this project is to implement an experimental prototype of a 2FA smart door lock system that mitigates the vulnerabilities of single-factor authentication. The system combines:

1. **Primary Authentication**: "Something you have" or "Something you know" (NFC card or PIN code).
2. **Secondary Authentication**: "Something you are" (Facial verification via vision AI).

**Scope of Implementation:**
- A hardware prototype utilizing an Arduino to manage a 125kHz/13.56MHz RFID/NFC reader, a matrix keypad, and a relay module.
- A centralized backend API for multi-stage authentication, event logging, and serial communication.
- A computer-vision module for facial verification.
- A monitoring dashboard to summarize validation attempts and system health.

**Out of Scope:**
- This prototype is **not** a certified commercial access-control product.
- Advanced commercial-grade anti-spoofing (e.g., depth-sensing 3D cameras).
- Physical enclosure design resistant to heavy physical tampering.

### Key Results

- **Two-Stage Verification:** Successfully implemented a sequential authentication pipeline where unlocking the relay requires both valid primary credentials and a subsequent positive facial match.
- **Relay Control:** Established controlled serial communication to command the Arduino relay only upon successful backend validation.
- **Auditing:** Developed a robust logging mechanism recording all successful and failed access attempts.
