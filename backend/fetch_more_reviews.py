"""
fetch_more_reviews.py — For unrated pubs, fetches fresh reviews using both
sort orders (most_relevant + newest) to maximise coverage, then rescores.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from database import get_connection
from places import fetch_reviews, save_reviews
from scorer import score_pub


def run():
    conn = get_connection()
    unrated = conn.execute("""
        SELECT p.id, p.name, p.place_id FROM pubs p
        JOIN scores s ON p.id = s.pub_id
        WHERE s.guinness_score IS NULL
    """).fetchall()
    conn.close()

    print(f"Fetching more reviews for {len(unrated)} unrated pubs...")

    for i, pub in enumerate(unrated, 1):
        print(f"[{i}/{len(unrated)}] {pub['name']}...", end=" ")

        # Delete existing reviews so we don't duplicate
        conn = get_connection()
        existing = conn.execute("SELECT COUNT(*) FROM reviews WHERE pub_id = ?", (pub["id"],)).fetchone()[0]
        conn.execute("DELETE FROM reviews WHERE pub_id = ?", (pub["id"],))
        conn.commit()
        conn.close()

        # Fetch with both sort orders (up to ~10 unique reviews)
        reviews = fetch_reviews(pub["place_id"])
        save_reviews(pub["id"], reviews)
        print(f"{len(reviews)} reviews (was {existing}) — scoring...")
        score_pub(pub["id"], pub["name"])

    conn = get_connection()
    now_rated = conn.execute("SELECT COUNT(*) FROM scores WHERE guinness_score IS NOT NULL").fetchone()[0]
    still_unrated = conn.execute("SELECT COUNT(*) FROM scores WHERE guinness_score IS NULL").fetchone()[0]
    conn.close()
    print(f"\nDone! Rated: {now_rated} | Still unrated: {still_unrated}")


if __name__ == "__main__":
    run()
