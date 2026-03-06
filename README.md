# 🍺 Guinness Rater — Melbourne

Finds pubs in Melbourne that serve Guinness, scores the quality using Google reviews + OpenAI, and displays everything on an interactive map.

## Prerequisites
- Python 3.10+
- Google Maps Platform API key (Places API enabled)
- OpenAI API key

## Setup

### 1. Clone & create your `.env`
```bash
cd guinness-rater
cp .env.example .env
# Edit .env and fill in your API keys
```

### 2. Install Python dependencies
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Collect data (runs once)
```bash
python collect_data.py
```
This will:
- Search Google Places for Guinness pubs in Melbourne
- Fetch reviews for each pub
- Score Guinness quality via OpenAI
- Store everything in `backend/guinness.db`

### 4. Start the backend API
```bash
uvicorn main:app --reload
# API runs at http://localhost:8000
```

### 5. Open the frontend
Open `frontend/index.html` in your browser.

## Map Legend
| Pin colour | Guinness score |
|---|---|
| 🟢 Green | 4.0 – 5.0 ★ |
| 🟠 Orange | 3.0 – 3.9 ★ |
| 🔴 Red | 1.0 – 2.9 ★ |
| ⚫ Grey | Not enough reviews to score |

## API Endpoints
- `GET /pubs` — All pubs with scores
- `GET /pubs/{id}` — Single pub detail with reviews
