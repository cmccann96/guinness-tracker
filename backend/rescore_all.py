"""rescore_all.py — Rescores every pub in the DB with the updated prompt."""
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from database import get_connection
from scorer import score_pub

conn = get_connection()
pubs = conn.execute("SELECT id, name FROM pubs").fetchall()
conn.close()

print(f"Rescoring all {len(pubs)} pubs...")
for i, pub in enumerate(pubs, 1):
    print(f"[{i}/{len(pubs)}] {pub['name']}...")
    score_pub(pub["id"], pub["name"])

conn = get_connection()
rated = conn.execute("SELECT COUNT(*) FROM scores WHERE guinness_score IS NOT NULL").fetchone()[0]
print(f"\nDone! {rated}/{len(pubs)} pubs scored.")
