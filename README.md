# iPant Future

Deployment-ready Vedic astrology web app.

## Stack
- Frontend: GitHub Pages from `/docs`
- Backend: FastAPI on Render from `/backend`
- Chart engine: Swiss Ephemeris + Lahiri ayanamsa
- AI layer: OpenAI Responses API for concise summaries only

## Deploy
GitHub Pages:
- Settings → Pages
- Source: Deploy from branch
- Branch: `main`
- Folder: `/docs`

Render:
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Required env vars:
- `OPENAI_API_KEY`
- `OPENAI_MODEL=gpt-5.4-mini`
