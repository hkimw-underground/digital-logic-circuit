#!/usr/bin/env python3
"""Seed demo users and per-user access logs for local UI validation."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from database import Database


def main() -> int:
    db = Database()
    try:
        users = db.seed_demo_data()
        print(f"Seeded {len(users)} demo users.")
        for user in users:
            stats = user.get("stats", {})
            print(
                f"- {user['username']} / UID {user['nfc_uid']} / "
                f"entries={stats.get('successful_entries', 0)} events={stats.get('total_events', 0)}"
            )
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
