"""
fetch_serpapi_reviews.py — Uses SerpAPI Google Maps Reviews to get up to 50+
reviews per pub for the unrated ones. Two API calls per pub:
  1. Google Maps search → get data_id
  2. Google Maps Reviews → get reviews
"""
import os
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from serpapi import GoogleSearch
from database import get_connection
from scorer import score_pub

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def get_data_id(pub_name: str, address: str) -> tuple[str | None, list]:
    """Search Google Maps via SerpAPI. Returns (data_id, reviews) from place_results."""
    query = f"{pub_name} Melbourne"
    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": SERPAPI_KEY,
    }
    results = GoogleSearch(params).get_dict()

    place = results.get("place_results", {})
    data_id = place.get("data_id")

    # Extract any reviews already in place_results
    reviews = []
    for r in place.get("user_reviews", {}).get("most_relevant", []):
        text = r.get("description", "").strip()
        if text:
            reviews.append({
                "author": r.get("username", ""),
                "text": text,
                "rating": r.get("rating", 0),
            })

    return data_id, reviews


def fetch_serpapi_reviews(data_id: str, max_reviews: int = 40) -> list:
    """Fetch reviews from Google Maps via SerpAPI using data_id."""
    reviews = []
    next_page_token = None

    while len(reviews) < max_reviews:
        params = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "api_key": SERPAPI_KEY,
            "sort_by": "2",  # newest first
        }
        if next_page_token:
            params["next_page_token"] = next_page_token

        results = GoogleSearch(params).get_dict()
        page_reviews = results.get("reviews", [])

        for r in page_reviews:
            text = r.get("snippet", "").strip()
            if text:
                reviews.append({
                    "author": r.get("username", ""),
                    "text": text,
                    "rating": r.get("rating", 0),
                })

        next_page_token = results.get("serpapi_pagination", {}).get("next_page_token")
        if not next_page_token or not page_reviews:
            break

        time.sleep(0.5)  # be polite

    return reviews


def save_reviews(pub_id: str, reviews: list):
    conn = get_connection()
    conn.execute("DELETE FROM reviews WHERE pub_id = ?", (pub_id,))
    for r in reviews:
        conn.execute(
            "INSERT INTO reviews (pub_id, author, text, rating) VALUES (?, ?, ?, ?)",
            (pub_id, r["author"], r["text"], r["rating"]),
        )
    conn.commit()
    conn.close()


def run():
    conn = get_connection()
    unrated = conn.execute("""
        SELECT p.id, p.name, p.address FROM pubs p
        JOIN scores s ON p.id = s.pub_id
        WHERE s.guinness_score IS NULL
    """).fetchall()
    conn.close()

    print(f"Fetching SerpAPI reviews for {len(unrated)} unrated pubs...")

    for i, pub in enumerate(unrated, 1):
        print(f"[{i}/{len(unrated)}] {pub['name']}...")

        data_id, initial_reviews = get_data_id(pub["name"], pub["address"])
        if not data_id:
            print(f"  ⚠ Could not find place on Google Maps, skipping.")
            continue

        # Fetch more reviews via the dedicated reviews endpoint
        more_reviews = fetch_serpapi_reviews(data_id)
        # Merge, deduplicate by text
        seen = {r["text"] for r in initial_reviews}
        for r in more_reviews:
            if r["text"] not in seen:
                initial_reviews.append(r)
                seen.add(r["text"])

        reviews = initial_reviews
        save_reviews(pub["id"], reviews)
        print(f"  Got {len(reviews)} reviews — scoring...")
        score_pub(pub["id"], pub["name"])
        time.sleep(0.5)

    conn = get_connection()
    now_rated = conn.execute("SELECT COUNT(*) FROM scores WHERE guinness_score IS NOT NULL").fetchone()[0]
    still_unrated = conn.execute("SELECT COUNT(*) FROM scores WHERE guinness_score IS NULL").fetchone()[0]
    conn.close()
    print(f"\nDone! Rated: {now_rated} | Still unrated: {still_unrated}")


if __name__ == "__main__":
    run()
