Data directory

- Purpose: holds local SQLite database files and backups generated during development/runtime.
- Git policy: DB binaries and backups are intentionally ignored via project .gitignore.
- Tracked files: this README and .gitkeep only (to keep the folder in git).

Ignored examples
- fast6.db, fast6.db-wal, fast6.db-shm
- *.sqlite, *.sqlite3, *.db, *.bak

Recreating the database
- Run the FastAPI backend; migrations run automatically on startup to create schema if missing.
- Alternatively, from project root:
  ```bash
  source .venv/bin/activate
  python -m backend.scripts.run_migrations
  python -m backend.scripts.seed_all   # optional: add sample data
  ```

Notes
- Do not commit real data dumps/backups to git.
- If you need to share fixtures, add small, anonymized CSVs under a tests/fixtures path (tracked) instead.
