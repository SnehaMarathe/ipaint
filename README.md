
# iPant Future !

Pro astrologer version of iPant Future with:

- premium static frontend for GitHub Pages in `/docs`
- FastAPI backend for Render/Railway/Fly
- Vedic astrology engine using Swiss Ephemeris
- Lahiri ayanamsa
- Ascendant, Moon sign, Nakshatra, Vimshottari dasha
- Rasi (D1) and Navamsha (D9) charts
- North Indian style kundli rendering in the browser
- unlimited AI Q&A grounded in the user chart

## Repo layout

- `docs/` static frontend for GitHub Pages
- `backend/` FastAPI app
- `.env.example` environment variables

## Frontend deploy

Publish `/docs` using GitHub Pages.

## Backend deploy

Works well on Render.

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Environment variables

Copy `.env.example` to `.env` in `backend/` or configure in your hosting provider.

## Local run

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

Open `docs/index.html` directly for quick testing, or serve it locally.

## Notes

- Geocoding uses OpenStreetMap Nominatim through `geopy`.
- Time zone is detected using `timezonefinder`.
- The frontend calls the backend through `window.IPANT_API_BASE` or `localStorage.ipant_api_base`.
