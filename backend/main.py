import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from database import init_db, get_connection

app = FastAPI(title="Guinness Rater API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/config")
def get_config():
    return {"stadia_api_key": os.getenv("STADIA_API_KEY", "")}


@app.get("/pubs")
def list_pubs():
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.id, p.name, p.address, p.lat, p.lng,
               s.guinness_score, s.summary
        FROM pubs p
        LEFT JOIN scores s ON p.id = s.pub_id
        ORDER BY s.guinness_score DESC NULLS LAST
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/pubs/{pub_id}")
def get_pub(pub_id: str):
    conn = get_connection()
    pub = conn.execute("""
        SELECT p.id, p.name, p.address, p.lat, p.lng,
               s.guinness_score, s.summary, s.scored_at
        FROM pubs p
        LEFT JOIN scores s ON p.id = s.pub_id
        WHERE p.id = ?
    """, (pub_id,)).fetchone()

    if not pub:
        conn.close()
        raise HTTPException(status_code=404, detail="Pub not found")

    reviews = conn.execute("""
        SELECT author, text, rating FROM reviews WHERE pub_id = ?
    """, (pub_id,)).fetchall()
    conn.close()

    result = dict(pub)
    result["reviews"] = [dict(r) for r in reviews]
    return result


# Serve frontend — must be after all API routes
@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
