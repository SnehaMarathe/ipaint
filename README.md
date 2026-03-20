# iPaint — Only Good News ✦

> *"The world is full of beautiful things happening right now. We find them all."*

iPaint is an AI-powered good news app that uses Claude (with live web search) to surface only uplifting, positive, constructive stories — across 10 categories, updated on demand.

---

## Project Structure

```
ipaint/
├── backend/                  # Express API server
│   ├── server.js             # Main server — proxies requests to Anthropic
│   ├── package.json
│   ├── .env.example          # Copy to .env and fill in your key
│   └── railway.json          # Railway deployment config
│
├── frontend/                 # Static HTML/CSS/JS app
│   ├── public/
│   │   └── index.html        # The entire frontend (single file)
│   ├── package.json
│   └── vercel.json           # Vercel deployment config
│
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions: CI + deploy on push to main
│
├── .gitignore
├── package.json              # Root: runs both with concurrently
└── README.md
```

---

## Local Development

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/ipaint.git
cd ipaint
```

### 2. Install all dependencies

```bash
npm run install:all
```

### 3. Set up your API key

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
FRONTEND_URL=http://localhost:3000
PORT=3001
```

Get your key at [console.anthropic.com](https://console.anthropic.com).

### 4. Run both frontend and backend

```bash
npm run dev
```

This starts:
- **Backend** → http://localhost:3001
- **Frontend** → http://localhost:3000

Open http://localhost:3000 in your browser.

---

## API Reference

### `GET /api/health`
Health check.
```json
{ "status": "ok", "service": "iPaint API", "timestamp": "..." }
```

### `GET /api/news/:category`
Fetch top 5 positive stories for a category.

**Valid categories:** `India`, `World`, `Science`, `Health`, `Environment`, `Technology`, `Business`, `Sports`, `Arts`, `Community`

```bash
curl http://localhost:3001/api/news/India
```

**Response:**
```json
{
  "category": "India",
  "stories": [
    {
      "id": 1,
      "isTop": true,
      "tag": "Innovation",
      "headline": "...",
      "deck": "...",
      "body": "...",
      "joyScore": 94,
      "source": "The Hindu",
      "sourceUrl": "https://...",
      "timeAgo": "2 hours ago"
    },
    ...
  ]
}
```

### `POST /api/news/search`
Custom topic search.

```bash
curl -X POST http://localhost:3001/api/news/search \
  -H "Content-Type: application/json" \
  -d '{"query": "clean energy breakthroughs India 2026"}'
```

---

## Deploying to Production

### Backend → Railway

1. Create an account at [railway.app](https://railway.app)
2. Create a new project → **Deploy from GitHub repo**
3. Select the `backend/` folder as the root
4. Add environment variables in Railway dashboard:
   - `ANTHROPIC_API_KEY` = your key
   - `FRONTEND_URL` = your Vercel URL (e.g. `https://ipaint.vercel.app`)
   - `NODE_ENV` = `production`
5. Railway gives you a URL like `https://ipaint-backend.up.railway.app`

### Frontend → Vercel

1. Create an account at [vercel.com](https://vercel.com)
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Add environment variable:
   - `IPAINT_API_URL` = your Railway backend URL
5. Deploy — Vercel gives you `https://ipaint.vercel.app`

### Auto-deploy via GitHub Actions

The included `ci.yml` workflow automatically deploys on every push to `main`.

Add these **GitHub repository secrets** (Settings → Secrets → Actions):

| Secret | Where to get it |
|--------|----------------|
| `RAILWAY_TOKEN` | Railway dashboard → Account → Tokens |
| `VERCEL_TOKEN` | Vercel dashboard → Account → Tokens |
| `VERCEL_ORG_ID` | Run `vercel whoami` after installing CLI |
| `VERCEL_PROJECT_ID` | Run `vercel inspect` in your project |

---

## Pushing to GitHub (first time)

```bash
# Inside the ipaint/ folder:
git init
git add .
git commit -m "feat: initial iPaint good news app"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/ipaint.git
git branch -M main
git push -u origin main
```

---

## Rate Limiting

The backend limits each IP to **30 requests per minute** to keep API costs under control. Adjust in `server.js`:

```js
const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 30,           // ← change this
});
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/CSS/JS (single file, no build step) |
| Backend | Node.js + Express |
| AI | Anthropic Claude (`claude-sonnet-4-20250514`) with web search |
| Deploy: Frontend | Vercel |
| Deploy: Backend | Railway |
| CI/CD | GitHub Actions |

---

## License

MIT — build on it, ship it, make the world read better news.
