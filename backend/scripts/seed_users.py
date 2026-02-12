#!/usr/bin/env python3
"""
Seed development users for local testing.
Adds the default test user (Phil) and optionally others when the DB is empty.
Usage: python -m backend.scripts.seed_users
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.database import add_user, get_user_by_name


def main() -> None:
    default_users = [
        ("Phil", None, True),   # Default test user, admin
        ("Alice", "alice@example.com", False),
        ("Bob", "bob@example.com", False),
    ]
    for name, email, is_admin in default_users:
        existing = get_user_by_name(name)
        if existing:
            print(f"User '{name}' already exists (ID: {existing['id']})")
        else:
            uid = add_user(name, email, is_admin)
            print(f"Added user '{name}' (ID: {uid})")
    print("Seed complete.")


if __name__ == "__main__":
    main()
