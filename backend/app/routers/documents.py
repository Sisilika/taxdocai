"""Upload + extraction endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.ocr import ocr_file
from app.services.structurer import structure_document
from app.models.schemas import ExtractedDocument

router = APIRouter()

# In-memory store for the demo. Swap for Postgres in production
# (see app/models for SQLAlchemy table definitions to add).
_DOCS: dict[str, ExtractedDocument] = {}


@router.post("/upload", response_model=ExtractedDocument)
async def upload_document(file: UploadFile = File(...)):
    """Upload a W-2/1099/K-1 PDF or image. Runs OCR -> structured extraction."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    file_bytes = await file.read()

    try:
        ocr_result = ocr_file(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(500, f"OCR failed: {e}")

    try:
        doc = structure_document(ocr_result["text"])
    except Exception as e:
        raise HTTPException(500, f"Structuring failed: {e}")

    _DOCS[doc.document_id] = doc
    return doc


@router.get("/{document_id}", response_model=ExtractedDocument)
def get_document(document_id: str):
    doc = _DOCS.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.put("/{document_id}", response_model=ExtractedDocument)
def update_document(document_id: str, updated: ExtractedDocument):
    """Human-in-the-loop edit: reviewer corrects extracted fields before submission."""
    if document_id not in _DOCS:
        raise HTTPException(404, "Document not found")
    _DOCS[document_id] = updated
    return updated


@router.get("/")
def list_documents():
    return list(_DOCS.values())
