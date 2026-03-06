"""
rescore_unrated.py — Re-scores only pubs that currently have no Guinness score.
Safe to run multiple times; won't touch already-scored pubs.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from database import get_connection
from scorer import score_pub


def run():
    conn = get_connection()
    unrated = conn.execute("""
        SELECT p.id, p.name FROM pubs p
        JOIN scores s ON p.id = s.pub_id
        WHERE s.guinness_score IS NULL
    """).fetchall()
    conn.close()

    print(f"Re-scoring {len(unrated)} unrated pubs...")
    for i, row in enumerate(unrated, 1):
        print(f"[{i}/{len(unrated)}] {row['name']}...")
        score_pub(row["id"], row["name"])

    conn = get_connection()
    now_rated = conn.execute("SELECT COUNT(*) FROM scores WHERE guinness_score IS NOT NULL").fetchone()[0]
    still_unrated = conn.execute("SELECT COUNT(*) FROM scores WHERE guinness_score IS NULL").fetchone()[0]
    conn.close()
    print(f"\nDone! Rated: {now_rated} | Still unrated: {still_unrated}")


if __name__ == "__main__":
    run()
