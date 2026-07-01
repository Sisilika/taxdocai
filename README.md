# TaxDocAI

AI-powered tax document automation platform — upload a W-2/1099/K-1, get
structured data extraction, automated validation against IRS rules (via
RAG), a human-in-the-loop review UI, and export to a tax-prep-ready
CSV/XML format.

**100% free stack:** Tesseract OCR + Groq free tier (llama-3.3-70b-versatile)
+ Chroma (embedded) + Render free tier (backend) + Vercel free tier (frontend).

## Architecture

```
Upload (PDF/image)
   │
   ▼
Tesseract OCR  ──────────────►  raw text + word boxes
   │
   ▼
Groq (llama-3.3-70b, tool-use)  ───►  structured ExtractedDocument JSON
   │
   ▼
React review UI  ◄──── human edits fields side-by-side with source image
   │
   ▼
Validation Agent:
   1. deterministic rule checks (format, sanity checks)
   2. RAG lookup against IRS instruction chunks (Chroma)
   3. Groq drafts a plain-English reviewer summary
   │
   ▼
Mock export connector  ───►  CSV / XML (stand-in for Drake/UltraTax import)
```

## Project layout
```
backend/        FastAPI app (extraction, agent, RAG, export)
frontend/       React + Vite review UI
sample_docs/    Place sample W-2/1099 test images/PDFs here
docs/           DEPLOY.md, INTEGRATION.md
render.yaml     Render.com one-click deploy config
```

## Run locally

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# requires tesseract-ocr + poppler installed locally:
#   brew install tesseract poppler        (macOS)
#   apt install tesseract-ocr poppler-utils  (Linux)
cp .env.example .env
# edit .env — add your free GROQ_API_KEY from console.groq.com
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE=http://localhost:8000
npm run dev
```

Open `http://localhost:5173`, upload a sample tax doc, review extracted
fields, run the validation agent, export.

## Deploy for free (live link for an interview)
See [`docs/DEPLOY.md`](docs/DEPLOY.md) — Render (backend) + Vercel (frontend).

## Notes / honest scope
- OCR uses Tesseract (free/open-source). Accuracy on skewed or low-res scans
  can be rough — the swap-in point for a vision-LLM upgrade is documented in
  `backend/app/services/ocr.py`.
- LLM layer uses Groq's free tier (`llama-3.3-70b-versatile`). Groq supports
  OpenAI-compatible tool-calling, so switching to any other provider that
  speaks the OpenAI API (OpenAI itself, Together, Fireworks, etc.) only
  requires changing the base URL and API key.
- RAG corpus is a seeded set of IRS guidance chunks in
  `backend/app/rag/knowledge_seed.py` — no external downloads needed.
- Storage is in-memory for the demo; swap for Postgres by adding SQLAlchemy
  models (schema is already fully Pydantic-typed).
- Mock connector + mapping notes for Drake/UltraTax are in
  [`docs/INTEGRATION.md`](docs/INTEGRATION.md).
