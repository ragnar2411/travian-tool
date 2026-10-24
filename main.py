from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import math
from datetime import datetime, timedelta

app = FastAPI(title="Travian Inactive Analyzer API")

# מאפשר לממשק ה-Frontend לתקשר עם ה-Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "travian_analyzer.db"

@app.get("/api/inactives")
def get_inactives(
    server: str,
    origin_x: int,
    origin_y: int,
    radius: int = 30,
    days: int = Query(3, ge=1, le=5),
    min_pop: int = 0,
    max_pop: int = 9999,
    excluded_alliances: str = ""
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    past_date_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    excluded_list = [a.strip().lower() for a in excluded_alliances.split(",") if a.strip()]
    
    # שאילתת SQL המבצעת בדיקה ברמת החשבון הכללי של השחקן
    query = '''
        WITH CurrentAccountPop AS (
            SELECT player_id, SUM(population) as total_pop_now
            FROM village_snapshots
            WHERE server_url = ? AND snapshot_date = ?
            GROUP BY player_id
        ),
        PastAccountPop AS (
            SELECT player_id, SUM(population) as total_pop_past
            FROM village_snapshots
            WHERE server_url = ? AND snapshot_date = ?
            GROUP BY player_id
        )
        SELECT 
            v.village_id, v.village_name, v.x, v.y, v.tribe, v.population,
            v.player_id, v.player_name, v.alliance_tag,
            c.total_pop_now, p.total_pop_past
        FROM village_snapshots v
        JOIN CurrentAccountPop c ON v.player_id = c.player_id
        JOIN PastAccountPop p ON v.player_id = p.player_id
        WHERE v.server_url = ? 
          AND v.snapshot_date = ?
          AND c.total_pop_now <= p.total_pop_past
          AND v.population BETWEEN ? AND ?
    '''
    
    try:
        cursor.execute(query, (server, today_str, server, past_date_str, server, today_str, min_pop, max_pop))
        rows = cursor.fetchall()
    except Exception as e:
        rows = []
    finally:
        conn.close()
    
    results = []
    for row in rows:
        v_id, v_name, x, y, tribe, pop, p_id, p_name, alliance, total_now, total_past = row
        
        # חישוב מרחק במפה
        dist = math.sqrt((x - origin_x)**2 + (y - origin_y)**2)
        if dist > radius:
            continue
            
        if alliance and alliance.lower() in excluded_list:
            continue
            
        results.append({
            "village_id": v_id,
            "village_name": v_name,
            "x": x,
            "y": y,
            "tribe": tribe,
            "population": pop,
            "player_name": p_name,
            "alliance_tag": alliance,
            "total_account_pop": total_now,
            "distance": round(dist, 1)
        })
        
    results.sort(key=lambda item: item["distance"])
    return {"status": "success", "count": len(results), "data": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)