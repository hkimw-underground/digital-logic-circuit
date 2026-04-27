---
sidebar_position: 1
---

# Threat Model

This section outlines the potential threats to the 2FA Smart Door Lock System, the expected impact, the implemented mitigations, and the remaining residual risks.

## Security Matrix

| Threat Actor / Action | Impact | Mitigation Strategy | Remaining Risk |
|---|---|---|---|
| **Unauthorized User with Stolen NFC Card** | High. System attempts primary auth. | System requires positive secondary authentication (Face Match). | If the attacker also visually resembles the user (or possesses a high-quality spoofing mechanism), access may be granted. |
| **Unauthorized User guessing PIN** | High. | Brute-force is hindered by secondary Face Match requirement. Invalid attempts are logged. | Physical damage to keypad from repeated use. |
| **Presentation Attack (Photo/Screen Spoofing)** | Critical. Bypass of biometric factor. | YOLOv8 model thresholding prevents blurry matches. | **High.** Standard 2D RGB cameras cannot reliably detect depth or liveness. A high-resolution tablet video could bypass the system. |
| **Serial Bus Tampering** | Critical. Injection of `UNLOCK` command. | None implemented in current software. | **High.** If the attacker accesses the USB cable between the Server and Arduino, they can send plaintext serial commands. |
| **Physical Relay Bypass** | Critical. Direct lock actuation. | Physical enclosure (Assumed). | **High.** If the attacker shorts the relay output terminals directly, the software cannot detect or prevent it. |
| **Power Interruption** | Moderate. Denial of service. | Use of fail-secure physical lock hardware. | Legitimate users cannot enter during a power outage unless mechanical override keys are provided. |

## Design Philosophy

The system adheres to the principle of "Fail-Secure". Software exceptions, missing hardware (e.g., camera disconnected), or communication timeouts default to a denied state. The relay remains disengaged unless a continuous, positive logic path completes successfully.
