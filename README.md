# iPant Future !

A GitHub-ready astrology web app for **www.ipant.in**.

This project includes:
- a premium landing page with the exact headline **iPant Future !**
- a real **Vedic / sidereal astrology engine** powered by **Swiss Ephemeris**
- birth chart generation from date, time, place, latitude, longitude, and timezone
- one **free** personalized question
- a **₹1 QR unlock** flow for each additional question
- an OpenAI-powered answer layer with a safe fallback when no API key is set

## What is production-ready and what is demo-ready

Production-ready:
- repo structure for GitHub
- `.gitignore`
- `.env.example`
- FastAPI backend
- real chart calculation using Swiss Ephemeris
- frontend UI and state flow
- QR generation for UPI-style payments

Demo-ready only:
- `/api/payment/confirm` manually unlocks one paid question
- for launch, replace it with a real payment provider webhook verification flow

## Project structure

```text
ipant-future-github-ready/
├── backend/
│   └── main.py
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Local setup

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Add environment variables

```bash
cp .env.example .env
```

Then fill in:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `UPI_ID`
- `PAYEE_NAME`

### 4) Run the app

```bash
uvicorn backend.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## How the chart engine works

The app uses **Swiss Ephemeris** with:
- **sidereal mode**
- **Lahiri ayanamsa**
- house cusps via `houses_ex`
- planet positions via `calc_ut`

This means the chart is based on a real astrology engine, not a fake text-only approximation.

## How the Q&A pricing flow works

1. User generates chart
2. User asks the first question for free
3. Any next question returns a payment-required response
4. Frontend shows a ₹1 QR code
5. Demo button confirms payment and unlocks one more answer
6. Repeat for each next question

### For production
Replace this endpoint:

```text
POST /api/payment/confirm
```

with:
- your UPI provider webhook
- signature verification
- transaction status validation
- session-based unlock crediting

## Recommended production improvements

- add persistent storage such as Postgres or Supabase for sessions and payment state
- add a real place lookup backend with rate limiting
- add webhook verification for your payment provider
- add image upload if you want users to upload an existing kundli or chart screenshot
- add server-side logging and abuse controls

## OpenAI API key: step by step

1. Sign in to the OpenAI API platform.
2. Create or open a project.
3. Go to **API keys**.
4. Create a new secret key.
5. Copy it once and save it securely.
6. Put it in your local `.env` file as `OPENAI_API_KEY`.
7. Never commit `.env` to GitHub.
8. For deployment, store it in your hosting provider's environment variable settings.

## Push this repo to GitHub

```bash
git init
git add .
git commit -m "Initial commit for iPant Future"
git branch -M main
git remote add origin https://github.com/SnehaMarathe/ipaint.git
git push -u origin main
```

## Notes

- The frontend uses Open-Meteo geocoding to help fill latitude, longitude, and timezone.
- If geocoding fails, the user can still type latitude, longitude, and timezone manually.
- The OpenAI layer is optional. If the API key is missing, the app still produces the chart and a basic reading.
