---
sidebar_position: 1
---

# Development Methodology

This appendix details the engineering methodology and iterative decisions made during the development of the 2FA prototype.

## Iterative Development Phases

The project was executed in sequential phases to isolate complexity:

### Phase 1: Hardware Abstraction
Initial development focused exclusively on Arduino firmware. The goal was to abstract the MFRC522 SPI communications and Matrix Keypad polling into a simple, reliable serial interface. This allowed the backend to treat the hardware rig as a black-box I/O stream.

### Phase 2: Core Authentication Logic
The Python backend was developed using Test-Driven Development (TDD) principles. SQLite with Write-Ahead Logging (WAL) was selected to provide concurrent read access for the dashboard without locking the primary authentication thread.

### Phase 3: Vision Integration
YOLOv8 was integrated for facial extraction due to its balance of speed and accuracy on standard CPU/Edge hardware. The initial implementation suffered from false positives in poorly lit environments; this was mitigated by implementing a strict confidence threshold and enforcing a minimum bounding-box size.

### Phase 4: System Integration
The final phase connected the serial manager to the vision pipeline. The most significant challenge was managing asynchronous serial timeouts while the vision module blocked the CPU. This was resolved by decoupling the serial listener into a dedicated background thread.
