import sqlite3
import requests
import re
import json

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

def fetch_live_game_servers():
    """שולף את כל השרתים הפעילים בזמן אמת מלובי המשחק"""
    servers = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    
    try:
        res = requests.get("https://lobby.travian.com/api/v1/servers", headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # מעבר על מבני הנתונים האפשריים שהלובי מחזיר
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("servers", data.get("response", data.get("data", [])))
                
            for s in items:
                if isinstance(s, dict):
                    domain = s.get("domain", s.get("url", s.get("name", "")))
                    if domain:
                        # ניקוי הדומיין במידה והוא מכיל https://
                        domain = domain.replace("https://", "").replace("http://", "").strip("/")
                        if "travian.com" in domain and domain not in servers:
                            servers.append(domain)
    except Exception as e:
        print(f"Lobby fetch error: {e}")

    # אם מסיבה כלשהי הלובי לא החזיר שרתים, נחזיר רשימה בסיסית כדי שהתפריט לא יהיה ריק
    if not servers:
        servers = [
            "rog.x5.international.travian.com",
            "rog.x1.arabics.travian.com",
            "ts3.x1.arabics.travian.com",
            "ts21.x2.arabics.travian.com"
        ]

    return list(set(servers))

def fetch_inactive_farms(server_domain="ts3.x1.arabics.travian.com", center_x=0, center_y=0, max_distance=30):
    init_db()
    
    map_url = f"https://{server_domain}/map.sql"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(map_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch map.sql from {server_domain}")
            return 0
        map_data = response.text
    except Exception as e:
        print(f"Error fetching map.sql: {e}")
        return 0

    pattern = re.compile(r"VALUES\s*\(([^)]+)\)")
    matches = pattern.findall(map_data)
    
    conn = sqlite3.connect("travian.db")
    cursor = conn.cursor()
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
                
                dist = round(((x - center_x)**2 + (y - center_y)**2)**0.5, 1)
                
                if dist <= max_distance and pop < 200 and pop > 0:
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
