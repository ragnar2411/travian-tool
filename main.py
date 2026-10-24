import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import os
from scraper import fetch_inactive_farms
import sqlite3

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Backend is Running!</h1><p>index.html not found.</p>"

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
def trigger_scan():
    try:
        count = fetch_inactive_farms()
        return {"status": "success", "added": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
