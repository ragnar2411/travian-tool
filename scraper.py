import requests
import re
import sqlite3
from datetime import datetime

# רשימת השרתים למעקב (תוכל להוסיף כאן כל כתובת שרת נוספת בטרויאן)
SERVERS = [
    "ts1.x3.international.travian.com",
    "ts3.x1.arabics.travian.com"
]

def parse_sql_insert(line):
    """חילוץ ערכים מתוך שורת INSERT של map.sql"""
    match = re.search(r"VALUES\s*\((.+)\)", line, re.IGNORECASE)
    if not match:
        return None
    
    raw_val = match.group(1)
    parts = re.findall(r"(?:'[^']*'|[^,]+)+", raw_val)
    
    try:
        x = int(parts[1].strip())
        y = int(parts[2].strip())
        tribe = int(parts[3].strip())
        village_id = int(parts[4].strip())
        village_name = parts[5].strip().strip("'")
        player_id = int(parts[6].strip())
        player_name = parts[7].strip().strip("'")
        alliance_id = int(parts[8].strip())
        alliance_tag = parts[9].strip().strip("'")
        population = int(parts[10].strip())
        
        return (village_id, x, y, tribe, village_name, player_id, player_name, alliance_id, alliance_tag, population)
    except Exception as e:
        return None

def fetch_server_map(server_url):
    print(f"Fetching map.sql from {server_url}...")
    url = f"https://{server_url}/map.sql"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch {url}: Status {response.status_code}")
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect("travian_analyzer.db")
        cursor = conn.cursor()
        
        records = []
        for line in response.text.splitlines():
            if line.startswith("INSERT INTO"):
                parsed = parse_sql_insert(line)
                if parsed:
                    v_id, x, y, tribe, v_name, p_id, p_name, a_id, a_tag, pop = parsed
                    records.append((server_url, v_id, x, y, tribe, v_name, p_id, p_name, a_id, a_tag, pop, today))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO village_snapshots 
            (server_url, village_id, x, y, tribe, village_name, player_id, player_name, alliance_id, alliance_tag, population, snapshot_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records)
        
        conn.commit()
        conn.close()
        print(f"Successfully processed {len(records)} villages for {server_url}.")
        
    except Exception as e:
        print(f"Error processing {server_url}: {e}")

def run_daily_update():
    for server in SERVERS:
        fetch_server_map(server)

if __name__ == "__main__":
    run_daily_update()