# iPant Future — Full Astrology Engine

Production-oriented Vedic astrology backend for **iPant Future**.

## What it does
- Geocodes birthplace to latitude/longitude
- Resolves timezone from coordinates
- Computes **sidereal Vedic chart** using **Swiss Ephemeris**
- Calculates:
  - Ascendant (Lagna)
  - Rasi / D1 chart
  - Navamsha / D9 chart
  - 9 graha sign placements
  - Whole-sign house placements from Lagna
  - Moon nakshatra + pada
  - Vimshottari mahadasha (current + next)
- Calls OpenAI only for a **short summarized interpretation**

## Architecture
- `backend/chart_engine.py` → real astrology calculations
- `backend/ai_summary.py` → OpenAI summary layer
- `backend/main.py` → FastAPI API
- `docs/` → optional static landing page / API smoke test

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## Required env vars
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (optional, default in code)

## API endpoints
- `GET /health`
- `POST /api/chart`
- `POST /api/reading`

## Sample request
```json
{
  "date_of_birth": "1980-05-13",
  "time_of_birth": "20:15",
  "birth_place": "Pune, India"
}
```

## Notes
- Uses **Lahiri ayanamsa**
- Uses **whole-sign houses** for stable Vedic display
- Vimshottari dasha is calculated from Moon nakshatra longitude
- For best reliability in production, cache geocoding results

## Deployment
- Frontend can go on GitHub Pages (`/docs`)
- Backend should be deployed separately on Render / Railway / VPS
