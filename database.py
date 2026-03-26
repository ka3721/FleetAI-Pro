import sqlite3

def connect_db():
    return sqlite3.connect("users.db", check_same_thread=False)

def create_table():
    conn = connect_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()