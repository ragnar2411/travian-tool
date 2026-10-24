import sqlite3

def init_db():
    conn = sqlite3.connect("travian.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT,
            village TEXT,
            population INTEGER,
            x INTEGER,
            y INTEGER,
            distance REAL,
            last_active TEXT
        )
    """)
    conn.commit()
    conn.close()

def fetch_inactive_farms():
    # פונקציית הסריקה (כרגע מכינה את הטבלה ומחזירה 0 רשומות חדשות עד שנחבר את הסקרייפר המלא)
    init_db()
    return 0
