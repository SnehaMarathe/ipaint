import express from "express";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app  = express();
const PORT = process.env.PORT || 3000;

// Serve the frontend from ../frontend/public
app.use(express.static(path.join(__dirname, "../frontend/public")));

// All routes serve index.html (SPA fallback)
app.get("*", (_req, res) => {
  res.sendFile(path.join(__dirname, "../frontend/public/index.html"));
});

app.listen(PORT, () => {
  console.log(`✦ iPaint running on http://localhost:${PORT}`);
});
