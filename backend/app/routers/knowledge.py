"""RAG Q&A endpoint, e.g. 'what does box 12 code D mean?'"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.store import query_knowledge

router = APIRouter()


class KnowledgeQuery(BaseModel):
    question: str


@router.post("/ask")
def ask_knowledge_base(q: KnowledgeQuery):
    hits = query_knowledge(q.question, n_results=3)
    return {"question": q.question, "results": hits}
