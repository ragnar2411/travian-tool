from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import os
import sqlite3
from scraper import fetch_inactive_farms

app = FastAPI(title="Travian Inactive Hunter")

# נתיב ראשי - מציג את ממשק המשתמש (index.html)
@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Travian Tool Backend is Running!</h1><p>index.html not found.</p>"

# API לקבלת רשימת החוות הלא פעילות
@app.get("/api/farms")
def get_farms():
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API להפעלת סריקה חדשה
@app.get("/api/scan")
def trigger_scan():
    try:
        count = fetch_inactive_farms()
        return {"status": "success", "message": f"Scan completed. Found/updated {count} farms."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
