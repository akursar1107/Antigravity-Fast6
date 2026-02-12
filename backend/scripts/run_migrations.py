from backend.database.migrations import run_migrations, get_connection

if __name__ == "__main__":
    conn = get_connection()
    stats = run_migrations()
    print("Migration stats:", stats)
