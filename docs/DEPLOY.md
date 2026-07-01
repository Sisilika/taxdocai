# Deploying TaxDocAI for Free

This gets you a live URL to share with an interviewer, at $0 infra cost.

## Prerequisites
- GitHub account
- Free Groq API key → https://console.groq.com (takes ~1 min, no credit card)
- Free Render.com account → https://render.com
- Free Vercel account → https://vercel.com

## 1. Get your free Groq API key
1. Go to https://console.groq.com → sign up → API Keys → Create API Key
2. Copy the key (starts with `gsk_...`) — you'll need it in step 3.

## 2. Push to GitHub
```bash
cd taxdocai
git init
git add .
git commit -m "Initial TaxDocAI"
# create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/taxdocai.git
git push -u origin main
```

## 3. Backend → Render.com (free tier)
1. render.com → New → Blueprint → connect your GitHub repo.
   Render detects `render.yaml` automatically.
2. When prompted, set the env var:
   - `GROQ_API_KEY` = the key from step 1
3. Deploy. Render installs `tesseract-ocr` and `poppler-utils` via the build
   command in `render.yaml`, then starts FastAPI.
4. Note your Render URL, e.g. `https://taxdocai-backend.onrender.com`

> **Note:** Render free tier sleeps after 15 min idle. First request after
> sleep takes ~30s. Fine for an interview demo — just mention it upfront.

## 4. Frontend → Vercel (free tier)
1. vercel.com → New Project → import your GitHub repo.
2. Set "Root Directory" to `frontend`.
3. Add environment variable:
   - `VITE_API_BASE` = your Render backend URL from step 3
4. Deploy. You'll get a URL like `https://taxdocai.vercel.app`.

**This is the link you give the interviewer.**

## 5. Smoke-test
- Open the Vercel URL
- Upload a sample W-2 image from `/sample_docs/`
- Confirm fields populate in the right panel
- Click "Run validation agent" — should return issues + summary
- Download CSV and XML exports

## Upgrading the LLM (optional)
The Groq client in `structurer.py` and `agent.py` uses the OpenAI-compatible
API format. To switch to any other provider:
1. Change `base_url` in the Groq client init to the provider's endpoint
2. Swap the `GROQ_API_KEY` env var name if needed
3. Change the `MODEL` string

No other code changes required.
