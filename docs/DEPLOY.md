# Deploying TaxDocAI for Free

This gets you a live URL to share with an interviewer, at $0 infra cost
(only your own Claude API usage during testing, a few cents).

## 1. Push to GitHub
```bash
cd taxdocai
git init
git add .
git commit -m "Initial TaxDocAI scaffold"
gh repo create taxdocai --public --source=. --push
# or create the repo on github.com and `git remote add origin ...` + push
```

## 2. Backend → Render.com (free tier)
1. Go to render.com → New → Blueprint → connect your GitHub repo. Render
   will detect `render.yaml` at the repo root automatically.
2. When prompted, set the `ANTHROPIC_API_KEY` env var (get one at
   console.anthropic.com).
3. Deploy. Render free tier installs `tesseract-ocr` and `poppler-utils`
   via the build command in `render.yaml`, then starts the FastAPI app.
4. Note the URL Render gives you, e.g. `https://taxdocai-backend.onrender.com`.
   First request after idle may take ~30s to wake up (free tier sleeps).

## 3. Frontend → Vercel (free tier)
1. Go to vercel.com → New Project → import the same GitHub repo.
2. Set "Root Directory" to `frontend`.
3. Add an environment variable: `VITE_API_BASE` = your Render backend URL
   from step 2.
4. Deploy. Vercel gives you a URL like `https://taxdocai.vercel.app` —
   **this is the link you give the interviewer.**

## 4. Smoke-test
- Open the Vercel URL, upload a sample W-2 image from `/sample_docs`.
- Confirm extraction populates the right panel, "Run validation agent"
  produces issues + summary, and CSV/XML export downloads correctly.

## Notes on free-tier limits
- Render free web services sleep after 15 min idle and cold-start slowly —
  fine for an interview demo, mention it if showing live.
- Chroma is filesystem-based here; on Render free tier the filesystem is
  ephemeral on redeploy, so the seeded knowledge base re-seeds automatically
  on first RAG query after a redeploy (see `seed_if_empty()` in
  `app/rag/store.py`) — no action needed.
- For something more persistent, swap Chroma for Supabase's free Postgres +
  pgvector tier instead; the `query_knowledge()` interface in
  `app/rag/store.py` is the only place that would need to change.
