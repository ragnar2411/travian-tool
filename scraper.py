import sqlite3
import requests
import re
from datetime import datetime

# הגדרת שרת ברירת מחדל ומרכז חיפוש (X, Y)
SERVER_DOMAIN = "ts3.x1.arabics.travian.com"
CENTER_X = 0
CENTER_Y = 0
MAX_DISTANCE = 30  # רדיוס משבצות לחיפוש חוות

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
    
    # 1. הורדת קובץ map.sql הרשמי מהשרת
    map_url = f"https://{SERVER_DOMAIN}/map.sql"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(map_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch map.sql from {SERVER_DOMAIN}")
            return 0
        map_data = response.text
    except Exception as e:
        print(f"Error fetching map.sql: {e}")
        return 0

    # 2. ניתוח שורות ה-INSERT מתוך map.sql
    # פורמט נפוץ: INSERT INTO `x_world` VALUES (id, x, y, tribe, vmid, village_name, player_id, player_name, alliance_id, alliance_name, pop, ...);
    pattern = re.compile(r"VALUES\s*\(([^)]+)\)")
    matches = pattern.findall(map_data)
    
    conn = sqlite3.connect("travian.db")
    cursor = conn.cursor()
    
    # ניקוי חוות ישנות לפני עדכון
    cursor.execute("DELETE FROM farms")
    
    added_count = 0
    for match in matches:
        parts = [p.strip(" '\"") for p in match.split(",")]
        if len(parts) >= 11:
            try:
                x = int(parts[1])
                y = int(parts[2])
                village_name = parts[5]
                player_name = parts[7]
                pop = int(parts[10])
                
                # חישוב מרחק מהמרכז
                dist = round(((x - CENTER_X)**2 + (y - CENTER_Y)**2)**0.5, 1)
                
                # סינון חוות: ברדיוס המוגדר ואוכלוסייה קטנה מ-200 (פוטנציאל לחווה לא פעילה)
                if dist <= MAX_DISTANCE and pop < 200 and pop > 0:
                    cursor.execute("""
                        INSERT INTO farms (player, village, population, x, y, distance, last_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (player_name, village_name, pop, x, y, dist, "Detected via Map"))
                    added_count += 1
            except (ValueError, IndexError):
                continue

    conn.commit()
    conn.close()
    return added_count
