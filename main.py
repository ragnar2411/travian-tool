from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import uvicorn
import os
import sqlite3
import threading
import time
from scraper import fetch_inactive_farms, fetch_live_game_servers

app = FastAPI()

def background_auto_updater():
    """פונקציית רקע שרצה כל 6 שעות ומעודכנת אוטומטית"""
    while True:
        try:
            print("Background task: Fetching live servers and updating...")
            servers = fetch_live_game_servers()
            if servers:
                default_server = servers[0]
                fetch_inactive_farms(server_domain=default_server, center_x=0, center_y=0, max_distance=30)
                print(f"Background task: Successfully updated farms from {default_server}")
        except Exception as e:
            print(f"Background task error: {e}")
        
        # המתנה של 6 שעות (6 שעות * 60 דקות * 60 שניות)
        time.sleep(6 * 60 * 60)

@app.on_event("startup")
def startup_event():
    """הפעלת משימת הרקע ברגע שהשרת עולה לאוויר"""
    updater_thread = threading.Thread(target=background_auto_updater, daemon=True)
    updater_thread.start()

@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Backend Running</h1>"

@app.get("/api/servers")
def get_servers():
    """מחזיר את כל השרתים הפעילים שנמשכו ישירות ממערכות המשחק"""
    servers = fetch_live_game_servers()
    return {"status": "success", "servers": servers}

@app.get("/api/farms")
def get_farms():
    conn = sqlite3.connect("travian.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, player, village, population, x, y, distance, last_active FROM farms ORDER BY distance ASC")
    rows = cursor.fetchall()
    conn.close()
    
    farms = []
    for row in rows:
        farms.append({
            "id": row[0],
            "player": row[1],
            "village": row[2],
            "population": row[3],
            "x": row[4],
            "y": row[5],
            "distance": row[6],
            "last_active": row[7]
        })
    return {"status": "success", "data": farms}

@app.post("/api/scan")
def trigger_scan(
    server: str = Query("ts3.x1.arabics.travian.com"),
    x: int = Query(0),
    y: int = Query(0),
    radius: int = Query(30)
):
    try:
        count = fetch_inactive_farms(server_domain=server, center_x=x, center_y=y, max_distance=radius)
        return {"status": "success", "added": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
