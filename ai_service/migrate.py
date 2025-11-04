"""
Database migration helper script
Run migrations easily without remembering Alembic commands
"""
import sys
import os
from alembic import command
from alembic.config import Config


def get_alembic_config():
    """Get Alembic configuration"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    alembic_cfg = Config(os.path.join(script_dir, "alembic.ini"))
    return alembic_cfg


def upgrade(revision="head"):
    """Upgrade database to a specific revision"""
    print(f"🔄 Upgrading database to revision: {revision}")
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, revision)
    print("✅ Database upgrade complete!")


def downgrade(revision="-1"):
    """Downgrade database by one revision"""
    print(f"⏪ Downgrading database to revision: {revision}")
    alembic_cfg = get_alembic_config()
    command.downgrade(alembic_cfg, revision)
    print("✅ Database downgrade complete!")


def current():
    """Show current database revision"""
    print("📍 Current database revision:")
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg)


def history():
    """Show migration history"""
    print("📜 Migration history:")
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg)


def create_migration(message):
    """Create a new migration"""
    print(f"📝 Creating new migration: {message}")
    alembic_cfg = get_alembic_config()
    command.revision(alembic_cfg, message=message, autogenerate=True)
    print("✅ Migration created!")


def main():
    """Main CLI handler"""
    if len(sys.argv) < 2:
        print("""
Database Migration Helper
=========================

Usage:
  python migrate.py upgrade          - Upgrade to latest revision
  python migrate.py downgrade        - Downgrade by one revision
  python migrate.py current          - Show current revision
  python migrate.py history          - Show migration history
  python migrate.py create "message" - Create new migration

Examples:
  python migrate.py upgrade
  python migrate.py create "add user table"
  python migrate.py downgrade
        """)
        return

    command_name = sys.argv[1].lower()

    if command_name == "upgrade":
        upgrade()
    elif command_name == "downgrade":
        downgrade()
    elif command_name == "current":
        current()
    elif command_name == "history":
        history()
    elif command_name == "create":
        if len(sys.argv) < 3:
            print("❌ Error: Please provide a migration message")
            print("Example: python migrate.py create 'add user table'")
            return
        message = sys.argv[2]
        create_migration(message)
    else:
        print(f"❌ Unknown command: {command_name}")
        print("Run 'python migrate.py' for usage instructions")


if __name__ == "__main__":
    main()
