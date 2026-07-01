"""
TaxDocAI - FastAPI entrypoint
Run locally:  uvicorn app.main:app --reload
Deployed on Render.com free tier (see /docs/DEPLOY.md)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import documents, agent, knowledge, export

app = FastAPI(
    title="TaxDocAI",
    description="AI-powered tax document extraction, validation, and review platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge (RAG)"])
app.include_router(export.router, prefix="/api/export", tags=["export"])


@app.get("/")
def root():
    return {"status": "ok", "service": "TaxDocAI backend"}


@app.get("/health")
def health():
    return {"status": "healthy"}
