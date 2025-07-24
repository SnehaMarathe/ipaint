# ipaint Backend

This is the backend for [ipaint.in](https://ipaint.in) – an initiative to send motivational messages to children.

## 🛠 Features
- Receives form submissions from frontend
- Stores messages in `wishes.json`
- Simple and lightweight Node.js + Express API

## 🧪 Local Setup

```bash
git clone https://github.com/<your-username>/ipaint-backend.git
cd ipaint-backend
npm install
cp .env.example .env  # Or create your own .env file
npm start
```

## 🌐 API Endpoints

- `POST /api/wishes` → Submit a new wish
- `GET /api/wishes` → View all wishes

## 📦 Deployment

Use Railway / Render / Vercel backend:
- Set `CLIENT_ORIGIN=https://ipaint.in` in env vars
