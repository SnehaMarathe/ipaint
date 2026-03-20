# iPaint — Only Good News ✦

> *"The world is full of beautiful things happening right now. We find them all."*

iPaint is a **completely free, zero-API-key** good news app. It pulls real stories from trusted RSS feeds (BBC, The Hindu, NASA, Times of India, Guardian, etc.) and scores each one with a built-in positivity filter — keeping only the bright stuff.

**No API keys. No backend needed. Just open `index.html`.**

---

## How it works

1. Fetches RSS feeds via [rss2json.com](https://rss2json.com) (free, no signup)
2. Scores every headline with a positivity word model (50+ positive signals, 30+ negative blockers)
3. Shows only stories that score ≥ 54 / 100, sorted by Joy Score
4. Click any story to read it — "Read Original" links to the real article

---

## Project Structure

```
ipaint/
├── frontend/
│   └── public/
│       └── index.html    ← The entire app. Open this in a browser.
├── backend/
│   ├── server.js         ← Optional: Express server to host the frontend
│   └── package.json
├── .github/
│   └── workflows/
│       └── ci.yml        ← Auto-deploy to GitHub Pages on push
├── .gitignore
├── package.json
└── README.md
```

---

## Run locally (simplest — no install needed)

Just open the file directly in your browser:

```
frontend/public/index.html
```

Double-click it. Done.

---

## Run with the Express server (optional)

```bash
cd backend
npm install
npm start
# → http://localhost:3000
```

---

## Deploy for free

### Option 1 — GitHub Pages (recommended, zero cost)

1. Push this repo to GitHub
2. Go to repo **Settings → Pages**
3. Set Source to **Deploy from a branch**
4. Set Branch to `main`, folder to `/frontend/public`
5. Your site is live at `https://SnehaMarathe.github.io/ipaint`

The included `ci.yml` does this automatically on every push to `main`.

### Option 2 — Netlify / Vercel

- Drag and drop the `frontend/public/` folder onto [netlify.com/drop](https://app.netlify.com/drop)
- Live in 30 seconds, free forever

---

## Feeds used

| Category     | Sources |
|-------------|---------|
| India        | Times of India, The Hindu, Livemint |
| World        | BBC World, The Guardian, NYT |
| Science      | Science Daily, NASA, New Scientist |
| Health       | Science Daily Health, WHO, WebMD |
| Environment  | The Guardian Env, Yale E360, Science Daily |
| Technology   | TechCrunch, MIT Tech Review, Wired |
| Business     | Economic Times, Entrepreneur, Livemint |
| Sports       | BBC Sport, Times of India Sports, ESPN Cricinfo |
| Arts         | The Guardian Culture, BBC Entertainment |
| Community    | Good News Network, Positive News |

---

## Tech stack

| | |
|---|---|
| Frontend | Pure HTML / CSS / JS — no framework, no build step |
| Data | RSS via rss2json.com (free tier) |
| Positivity filter | Custom keyword scoring — no ML, no cloud |
| Hosting | GitHub Pages (free) |
| API keys required | **None** |

---

MIT License — paint it, ship it, spread the good news.
