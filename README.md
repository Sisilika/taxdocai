# TaxDocAI

AI-powered tax document automation platform — upload a W-2/1099/K-1, get
structured data extraction, automated validation against IRS rules (via
RAG), a human-in-the-loop review UI, and export to a tax-prep-ready
CSV/XML format.

Built to demonstrate: document extraction (OCR + LLM structuring), a RAG
knowledge base + multi-step agent (extract → validate → flag → summarize),
a React review UI, a mock integration connector, and a deployable FastAPI
backend.

## Architecture

```
Upload (PDF/image)
   │
   ▼
Tesseract OCR  ──────────────►  raw text + word boxes
   │
   ▼
Claude (tool-use/function calling)  ───►  structured ExtractedDocument JSON
   │
   ▼
React review UI  ◄──── human edits fields side-by-side with source image
   │
   ▼
Validation Agent:
   1. deterministic rule checks (format, sanity checks)
   2. RAG lookup against IRS instruction chunks (Chroma)
   3. Claude drafts a plain-English reviewer summary
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
# requires tesseract-ocr + poppler installed locally, e.g.:
#   brew install tesseract poppler        (macOS)
#   apt install tesseract-ocr poppler-utils  (Linux)
cp .env.example .env   # add your ANTHROPIC_API_KEY
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
See [`docs/DEPLOY.md`](docs/DEPLOY.md) — Render (backend) + Vercel (frontend),
$0 infra cost.

## Notes / honest scope
- OCR uses Tesseract (free/open-source) as requested. It's noticeably less
  accurate than a vision-LLM-based extractor on skewed or low-res scans —
  that tradeoff and the swap-in point are documented in
  `backend/app/services/ocr.py`.
- RAG corpus is a small seeded set of hand-written IRS guidance chunks
  (`backend/app/rag/knowledge_seed.py`) so the demo runs with zero external
  downloads; swap in real IRS instruction PDFs for production.
- Storage is in-memory for the demo (`_DOCS` dict in `documents.py`); swap
  for Postgres for persistence — schema is already Pydantic-typed, so adding
  a SQLAlchemy mirror is mechanical.
- Mock connector + mapping notes for real Drake/UltraTax integration are in
  [`docs/INTEGRATION.md`](docs/INTEGRATION.md).
