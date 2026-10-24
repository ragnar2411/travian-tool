import sqlite3
import requests
import re
from datetime import datetime

# רשימת השרתים לחיפוש/מעקב (ניתן להוסיף כתובות שרתים נוספות בטראוויאן)
SERVERS = [
    "ts1.x3.international.travian.com",
    "ts3.x1.arabics.travian.com"
]

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
    init_db()
    conn = sqlite3.connect("travian.db")
    cursor = conn.cursor()
    
    # דוגמה להוספת נתוני הדגמה / סריקה לטבלה (כדי שיהיה מה להציג בממשק)
    # בהמשך נחבר את זה ל-API או לסקריפט הסריקה המלא שפיתחת
    sample_farms = [
        ("Player1", "Village A", 150, 12, -15, 4.2, "2 days ago"),
        ("Player2", "Village B", 85, 14, -18, 5.8, "5 days ago"),
        ("Player3", "Village C", 210, 10, -12, 2.1, "1 day ago")
    ]
    
    added_count = 0
    for farm in sample_farms:
        # בדיקה שהחווה לא קיימת כבר כדי לא ליצור כפילויות
        cursor.execute("SELECT id FROM farms WHERE player = ? AND village = ?", (farm[0], farm[1]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO farms (player, village, population, x, y, distance, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, farm)
            added_count += 1
            
    conn.commit()
    conn.close()
    return added_count
