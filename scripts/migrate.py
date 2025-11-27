#!/usr/bin/env python
"""Database migration runner script.

Usage:
    python scripts/migrate.py upgrade head     # Apply all migrations
    python scripts/migrate.py downgrade -1    # Rollback one migration
    python scripts/migrate.py current         # Show current revision
    python scripts/migrate.py history         # Show migration history
    python scripts/migrate.py revision -m "description"  # Create new migration
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from alembic import command
from alembic.config import Config


def get_alembic_config() -> Config:
    """Get Alembic configuration.
    
    Returns:
        Alembic Config object.
    """
    # Find alembic.ini relative to this script
    root_dir = Path(__file__).parent.parent
    alembic_ini = root_dir / "alembic.ini"
    
    if not alembic_ini.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini}")
    
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(root_dir / "alembic"))
    
    return config


def upgrade(revision: str = "head") -> None:
    """Upgrade database to a revision.
    
    Args:
        revision: Target revision (default: head).
    """
    config = get_alembic_config()
    command.upgrade(config, revision)
    print(f"✓ Upgraded to {revision}")


def downgrade(revision: str = "-1") -> None:
    """Downgrade database by revision steps.
    
    Args:
        revision: Target revision or steps (default: -1).
    """
    config = get_alembic_config()
    command.downgrade(config, revision)
    print(f"✓ Downgraded to {revision}")


def current() -> None:
    """Show current database revision."""
    config = get_alembic_config()
    command.current(config, verbose=True)


def history() -> None:
    """Show migration history."""
    config = get_alembic_config()
    command.history(config, verbose=True)


def revision(message: str, autogenerate: bool = True) -> None:
    """Create a new migration revision.
    
    Args:
        message: Migration description.
        autogenerate: Auto-detect schema changes.
    """
    config = get_alembic_config()
    command.revision(config, message=message, autogenerate=autogenerate)
    print(f"✓ Created new revision: {message}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database migration runner")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument(
        "revision", nargs="?", default="head", help="Target revision"
    )
    
    # downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument(
        "revision", nargs="?", default="-1", help="Target revision or steps"
    )
    
    # current command
    subparsers.add_parser("current", help="Show current revision")
    
    # history command
    subparsers.add_parser("history", help="Show migration history")
    
    # revision command
    revision_parser = subparsers.add_parser("revision", help="Create new revision")
    revision_parser.add_argument("-m", "--message", required=True, help="Description")
    revision_parser.add_argument(
        "--no-autogenerate", action="store_true", help="Disable autogenerate"
    )
    
    args = parser.parse_args()
    
    if args.command == "upgrade":
        upgrade(args.revision)
    elif args.command == "downgrade":
        downgrade(args.revision)
    elif args.command == "current":
        current()
    elif args.command == "history":
        history()
    elif args.command == "revision":
        revision(args.message, autogenerate=not args.no_autogenerate)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
