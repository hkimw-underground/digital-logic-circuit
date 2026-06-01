#!/usr/bin/env python3
"""Print connected USB serial ports for Arduino and ESP32-CAM setup."""

from __future__ import annotations

import argparse

try:
    from serial.tools import list_ports
except Exception as exc:
    raise SystemExit(f"pyserial list_ports unavailable: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Include non-USB ttyS ports.")
    args = parser.parse_args()

    ports = list(list_ports.comports())
    if not args.all:
        ports = [
            port for port in ports
            if "/ttyUSB" in port.device or "/ttyACM" in port.device or "USB" in str(port.hwid or "")
        ]
    if not ports:
        print("No USB serial ports detected.")
        return 1

    for port in ports:
        details = " | ".join(
            str(value or "-")
            for value in (
                port.device,
                port.description,
                port.hwid,
                getattr(port, "manufacturer", ""),
                getattr(port, "product", ""),
            )
        )
        print(details)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
