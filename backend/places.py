import httpx
import os
from database import get_connection

MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"

MELBOURNE_LOCATION = "-37.8136,144.9631"
SEARCH_RADIUS = 20000  # 20km radius around Melbourne CBD


def search_guinness_pubs():
    """Search Google Places for pubs in Melbourne that mention Guinness."""
    pubs = []
    params = {
        "query": "pub Guinness Melbourne",
        "location": MELBOURNE_LOCATION,
        "radius": SEARCH_RADIUS,
        "key": MAPS_API_KEY,
    }

    while True:
        response = httpx.get(PLACES_SEARCH_URL, params=params)
        data = response.json()

        for place in data.get("results", []):
            pubs.append({
                "id": place["place_id"],
                "name": place["name"],
                "address": place.get("formatted_address", ""),
                "lat": place["geometry"]["location"]["lat"],
                "lng": place["geometry"]["location"]["lng"],
                "place_id": place["place_id"],
            })

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break
        # Google requires a short delay before using next_page_token
        import time; time.sleep(2)
        params = {"pagetoken": next_page_token, "key": MAPS_API_KEY}

    return pubs


def fetch_reviews(place_id: str):
    """Fetch reviews for a place from Google Places Details API.
    Calls twice (most_relevant + newest) to maximise unique reviews returned."""
    seen = set()
    reviews = []

    for sort_order in ["most_relevant", "newest"]:
        params = {
            "place_id": place_id,
            "fields": "review",
            "reviews_sort": sort_order,
            "key": MAPS_API_KEY,
        }
        response = httpx.get(PLACES_DETAIL_URL, params=params)
        data = response.json()
        for r in data.get("result", {}).get("reviews", []):
            text = r.get("text", "").strip()
            if text and text not in seen:
                seen.add(text)
                reviews.append({
                    "author": r.get("author_name", ""),
                    "text": text,
                    "rating": r.get("rating", 0),
                })

    return reviews


def save_pub(pub: dict):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO pubs (id, name, address, lat, lng, place_id)
        VALUES (:id, :name, :address, :lat, :lng, :place_id)
    """, pub)
    conn.commit()
    conn.close()


def save_reviews(pub_id: str, reviews: list):
    conn = get_connection()
    for r in reviews:
        conn.execute("""
            INSERT INTO reviews (pub_id, author, text, rating)
            VALUES (?, ?, ?, ?)
        """, (pub_id, r["author"], r["text"], r["rating"]))
    conn.commit()
    conn.close()
