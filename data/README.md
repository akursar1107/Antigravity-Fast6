Data directory

- Purpose: holds local SQLite database files and backups generated during development/runtime.
- Git policy: DB binaries and backups are intentionally ignored via project .gitignore.
- Tracked files: this README and .gitkeep only (to keep the folder in git).

Ignored examples
- fast6.db, fast6.db-wal, fast6.db-shm
- *.sqlite, *.sqlite3, *.db, *.bak

Recreating the database
- Run the Streamlit app; the app calls init_db() on startup to create schema if missing.
- Alternatively, import and run init_db() manually:

  ```bash
  "/home/akursar/Documents/Antigravity Projects/Fast6/.venv/bin/python" - <<'PY'
  import sys; sys.path.append('src')
  from database import init_db
  init_db()
  print('DB initialized')
  PY
  ```

Notes
- Do not commit real data dumps/backups to git.
- If you need to share fixtures, add small, anonymized CSVs under a tests/fixtures path (tracked) instead.
