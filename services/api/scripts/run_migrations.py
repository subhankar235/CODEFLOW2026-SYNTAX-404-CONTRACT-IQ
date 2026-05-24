#!/usr/bin/env python
"""
Migration runner script - Apply all pending Alembic migrations.

Usage:
    cd services/api
    python -m scripts.run_migrations upgrade head
    python -m scripts.run_migrations current
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config
from app.core.config import settings


def get_alembic_config():
    """Get Alembic configuration."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return alembic_cfg


def main():
    """Run Alembic command from arguments."""
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.run_migrations <command> [args]")
        print("Commands: upgrade, downgrade, current, heads, history, show")
        sys.exit(1)

    alembic_cfg = get_alembic_config()
    cmd = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    try:
        if cmd == "upgrade":
            revision = args[0] if args else "head"
            print(f"Upgrading to {revision}...")
            command.upgrade(alembic_cfg, revision)
            print(f"✓ Successfully upgraded to {revision}")

        elif cmd == "downgrade":
            revision = args[0] if args else "-1"
            print(f"Downgrading to {revision}...")
            command.downgrade(alembic_cfg, revision)
            print(f"✓ Successfully downgraded to {revision}")

        elif cmd == "current":
            print("Current database revision:")
            command.current(alembic_cfg)

        elif cmd == "heads":
            print("Head revisions:")
            command.heads(alembic_cfg)

        elif cmd == "history":
            print("Migration history:")
            command.history(alembic_cfg)

        elif cmd == "show":
            revision = args[0] if args else "head"
            print(f"Migration details for {revision}:")
            command.show(alembic_cfg, revision)

        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
