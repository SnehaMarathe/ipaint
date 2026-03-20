import express from "express";
import cors from "cors";
import helmet from "helmet";
import rateLimit from "express-rate-limit";
import Anthropic from "@anthropic-ai/sdk";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// ── ANTHROPIC CLIENT ────────────────────────────────────────────────
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

// ── MIDDLEWARE ──────────────────────────────────────────────────────
app.use(helmet());
app.use(express.json());
app.use(
  cors({
    origin: process.env.FRONTEND_URL || "http://localhost:3000",
    methods: ["GET", "POST"],
  })
);

// Rate limiter: 30 requests per minute per IP
const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: "Too many requests. Please slow down." },
});
app.use("/api/", limiter);

// ── CATEGORY CONFIG ─────────────────────────────────────────────────
const CATEGORY_QUERIES = {
  India:
    "positive good news India achievement breakthrough today 2026",
  World:
    "positive uplifting world news breakthrough peace today 2026",
  Science:
    "science discovery breakthrough good news research 2026",
  Health:
    "medical health breakthrough cure treatment positive news 2026",
  Environment:
    "environment climate solution conservation renewable energy win 2026",
  Technology:
    "technology innovation positive impact humanity news 2026",
  Business:
    "business success economic growth jobs positive India news 2026",
  Sports:
    "sports win achievement inspiring athlete record 2026",
  Arts:
    "arts culture achievement music film award India 2026",
  Community:
    "community kindness hero grassroots positive story 2026",
};

// ── BUILD PROMPT ────────────────────────────────────────────────────
function buildPrompt(searchQuery, displayCat) {
  return `You are the editor of "iPaint" — a news app that ONLY publishes uplifting, positive, hopeful, constructive news.

Search the web and find the TOP 5 most genuinely positive, real, recent news stories related to: "${searchQuery}"

Requirements:
- All 5 stories must be 100% positive, uplifting, constructive
- They must be REAL, plausible, specific stories (real places, names, numbers)
- Reflect recent events from 2025-2026 where possible
- Story #1 (isTop: true) should be the MOST impactful/inspiring — give it a longer body (4 paragraphs)
- Stories #2-5 (isTop: false) get 2-paragraph bodies
- Include a realistic source name (e.g. "Reuters", "The Hindu", "BBC", "Times of India")
- Vary the angle: don't make all 5 about the same sub-topic

Return ONLY valid JSON — no markdown, no backticks, no preamble:
{
  "category": "${displayCat}",
  "stories": [
    {
      "id": 1,
      "isTop": true,
      "tag": "<short category tag>",
      "headline": "<compelling positive headline>",
      "deck": "<2-sentence uplifting summary>",
      "body": "<4 paragraphs, rich detail, positive framing>",
      "joyScore": <85-99>,
      "source": "<publication name>",
      "sourceUrl": "<plausible URL>",
      "timeAgo": "<e.g. '3 hours ago' or 'Today' or 'Yesterday'>"
    },
    {
      "id": 2, "isTop": false,
      "tag": "...", "headline": "...", "deck": "...",
      "body": "<2 paragraphs>",
      "joyScore": <80-97>,
      "source": "...", "sourceUrl": "...", "timeAgo": "..."
    },
    ... stories 3, 4, 5 same structure as story 2
  ]
}`;
}

// ── ROUTES ──────────────────────────────────────────────────────────

// Health check
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "iPaint API", timestamp: new Date().toISOString() });
});

// Get news by category
app.get("/api/news/:category", async (req, res) => {
  const { category } = req.params;
  const query = CATEGORY_QUERIES[category];

  if (!query) {
    return res.status(400).json({ error: `Unknown category: ${category}` });
  }

  await fetchNews(query, category, res);
});

// Custom search
app.post("/api/news/search", async (req, res) => {
  const { query } = req.body;

  if (!query || typeof query !== "string" || query.trim().length < 2) {
    return res.status(400).json({ error: "Query must be at least 2 characters." });
  }

  if (query.length > 200) {
    return res.status(400).json({ error: "Query too long (max 200 chars)." });
  }

  await fetchNews(query.trim(), "Custom Search", res);
});

// ── FETCH NEWS (shared logic) ────────────────────────────────────────
async function fetchNews(searchQuery, displayCat, res) {
  try {
    const prompt = buildPrompt(searchQuery, displayCat);

    // Try with web search first
    let text = "";
    try {
      const response = await anthropic.messages.create({
        model: "claude-sonnet-4-20250514",
        max_tokens: 2000,
        tools: [{ type: "web_search_20250305", name: "web_search" }],
        messages: [{ role: "user", content: prompt }],
      });

      text = response.content
        .filter((b) => b.type === "text")
        .map((b) => b.text)
        .join("");
    } catch (searchErr) {
      // Fallback: no web search
      console.warn("Web search failed, falling back:", searchErr.message);
      const response = await anthropic.messages.create({
        model: "claude-sonnet-4-20250514",
        max_tokens: 2000,
        messages: [{ role: "user", content: prompt }],
      });
      text = response.content
        .filter((b) => b.type === "text")
        .map((b) => b.text)
        .join("");
    }

    // Extract JSON
    const jsonMatch = text.replace(/```json|```/g, "").match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in Claude response");
    }

    const parsed = JSON.parse(jsonMatch[0]);

    // Validate structure
    if (!parsed.stories || !Array.isArray(parsed.stories) || parsed.stories.length === 0) {
      throw new Error("Invalid stories structure");
    }

    return res.json(parsed);
  } catch (err) {
    console.error("fetchNews error:", err.message);
    return res.status(500).json({
      error: "Failed to fetch news. Please try again.",
      detail: process.env.NODE_ENV === "development" ? err.message : undefined,
    });
  }
}

// ── START ────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`✦ iPaint API running on port ${PORT}`);
});
