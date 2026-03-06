import os
from openai import OpenAI
from datetime import datetime, timezone
from database import get_connection

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """You are an expert, brutally honest Guinness quality judge assessing Melbourne pubs.
You will be given a pub name and its customer reviews. Give a precise Guinness quality score.

SCORING RULES — use the FULL range, be nuanced and specific:
- 4.6 – 5.0 : Exceptional. Multiple reviews praising perfect pour, correct temperature, creamy head, well-maintained lines. Rare.
- 4.0 – 4.5 : Very good. Consistent praise, maybe one minor complaint.
- 3.3 – 3.9 : Decent. Mixed reviews, some good some average. Typical pub standard.
- 2.5 – 3.2 : Below average. Complaints about flatness, wrong temperature, poor pour technique.
- 1.0 – 2.4 : Bad. Multiple complaints about terrible Guinness specifically.

IMPORTANT: Do NOT round to nearest 0.5. Use precise decimals like 3.7, 4.2, 2.8, 4.6.
Most pubs should score between 3.0 and 4.2. Only award 4.5+ if reviews are genuinely outstanding.

Evidence priority:
1. Direct Guinness mentions — most weight
2. Stout / dark beer / draught mentions — strong proxy
3. General beer/pint quality — weaker proxy
4. Irish pub name with good general reviews — moderate positive signal

Write a single sentence summary. Note if score is inferred rather than based on direct Guinness mentions.

Respond in this exact JSON format:
{"score": 3.7, "summary": "Decent pint reported but complaints about inconsistent temperature drag the score down."}

Only return null score if there is truly zero useful information:
{"score": null, "summary": "Not enough information to estimate Guinness quality."}
"""


def extract_guinness_snippets(reviews: list) -> list:
    """Filter reviews relevant to beer/pint quality."""
    keywords = [
        "guinness", "stout", "pint", "black stuff", "draught", "draft",
        "beer", "ale", "tap", "pour", "head", "creamy", "flat", "cold",
        "bar", "drink", "drinks", "pub", "lager"
    ]
    return [
        r["text"] for r in reviews
        if any(kw in r["text"].lower() for kw in keywords)
    ]


def score_pub(pub_id: str, pub_name: str):
    """Pull reviews for a pub, score Guinness quality via LLM, store result."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT text, rating FROM reviews WHERE pub_id = ?", (pub_id,)
    ).fetchall()
    conn.close()

    reviews = [{"text": row["text"], "rating": row["rating"]} for row in rows]
    # Pass all reviews so the LLM has full context; prefer Guinness-specific snippets first
    guinness_snippets = extract_guinness_snippets(reviews)
    all_texts = [r["text"] for r in reviews]
    # Put Guinness-relevant reviews first, then fill with others up to 10
    ordered = guinness_snippets + [t for t in all_texts if t not in guinness_snippets]
    snippet_text = "\n---\n".join(ordered[:10])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Pub: {pub_name}\n\nReviews:\n{snippet_text}"},
        ],
        response_format={"type": "json_object"},
    )

    import json
    result = json.loads(response.choices[0].message.content)
    save_score(pub_id, result.get("score"), result.get("summary", ""))


def save_score(pub_id: str, score, summary: str):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO scores (pub_id, guinness_score, summary, scored_at)
        VALUES (?, ?, ?, ?)
    """, (pub_id, score, summary, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()
