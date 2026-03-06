"""
collect_data.py — Run this once to populate the database.
Searches Melbourne for Guinness pubs, fetches reviews, scores with LLM.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from database import init_db
from places import search_guinness_pubs, fetch_reviews, save_pub, save_reviews
from scorer import score_pub


def run():
    print("Initialising database...")
    init_db()

    print("Searching for Guinness pubs in Melbourne...")
    pubs = search_guinness_pubs()
    print(f"Found {len(pubs)} pubs.")

    for i, pub in enumerate(pubs, 1):
        print(f"[{i}/{len(pubs)}] {pub['name']} — fetching reviews...")
        save_pub(pub)
        reviews = fetch_reviews(pub["place_id"])
        save_reviews(pub["id"], reviews)

        print(f"  Scoring Guinness quality...")
        score_pub(pub["id"], pub["name"])

    print("Done! Data collection complete.")


if __name__ == "__main__":
    run()
