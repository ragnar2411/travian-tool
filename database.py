import sqlite3

DB_NAME = "travian_analyzer.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # טבלת סנאפשוטים של כפרים وشחקנים
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS village_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_url TEXT,
            village_id INTEGER,
            x INTEGER,
            y INTEGER,
            tribe INTEGER,
            village_name TEXT,
            player_id INTEGER,
            player_name TEXT,
            alliance_id INTEGER,
            alliance_tag TEXT,
            population INTEGER,
            snapshot_date DATE,
            UNIQUE(server_url, village_id, snapshot_date)
        )
    ''')
    
    # אינדקסים לביצועים מהירים בשאילתות גיאוגרפיות ותאריכים
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_server_date ON village_snapshots(server_url, snapshot_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_player ON village_snapshots(server_url, player_id, snapshot_date)')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()