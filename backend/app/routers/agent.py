"""Agent endpoints: run validation/anomaly/summary agent over an extracted doc."""
from fastapi import APIRouter, HTTPException

from app.routers.documents import _DOCS
from app.services.agent import run_agent
from app.models.schemas import AgentReviewResult

router = APIRouter()


@router.post("/review/{document_id}", response_model=AgentReviewResult)
def review_document(document_id: str):
    doc = _DOCS.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return run_agent(doc)
