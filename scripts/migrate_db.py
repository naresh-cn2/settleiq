#!/usr/bin/env python3
"""Database migration script for SettleIQ.

This script runs database migrations explicitly, suitable for deployment pipelines.
It should be run once during deployment, before starting the application servers.

Usage:
    SETTLEIQ_DB_PATH=postgresql://... python scripts/migrate_db.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from settleiq.persistence.store import open_store


def main() -> int:
    dsn = os.environ.get("SETTLEIQ_DB_PATH")
    if not dsn:
        print("ERROR: SETTLEIQ_DB_PATH environment variable not set", file=sys.stderr)
        return 1

    print(f"Running migrations for: {dsn.split('@')[-1] if '@' in dsn else dsn}")

    try:
        store = open_store(dsn)
        # The open_store function will run migrations automatically
        # but we can also explicitly call migrate to be sure
        if hasattr(store, 'migrate'):
            store.migrate()
        print("Migrations completed successfully")
        return 0
    except Exception as e:
        print(f"ERROR: Migration failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())