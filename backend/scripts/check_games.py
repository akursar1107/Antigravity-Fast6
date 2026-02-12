import sqlite3
import os

import sqlite3
import os

possible_paths = ["data/fast6.db", "src/data/fast6.db"]
db_path = None

for p in possible_paths:
    if os.path.exists(p):
        db_path = p
        break

if not db_path:
    print(f"Database not found at any of {possible_paths}")
    exit(1)

print(f"Checking database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check games
if ('games',) in tables:
    cursor.execute("SELECT COUNT(*) FROM games")
    count = cursor.fetchone()[0]
    print(f"Games count: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM games LIMIT 3")
        rows = cursor.fetchall()
        print("Sample games:", rows)
else:
    print("Games table not found.")

conn.close()
