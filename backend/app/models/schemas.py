"""Pydantic models representing extracted tax document fields."""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class DocType(str, Enum):
    W2 = "W-2"
    F1099_NEC = "1099-NEC"
    F1099_INT = "1099-INT"
    F1099_DIV = "1099-DIV"
    K1 = "K-1"
    UNKNOWN = "UNKNOWN"


class ExtractedField(BaseModel):
    box_label: str
    value: str
    confidence: float = Field(ge=0, le=1)
    source_bbox: Optional[List[float]] = None  # [x0, y0, x1, y1] on source image, for UI highlighting


class ExtractedDocument(BaseModel):
    document_id: str
    doc_type: DocType
    employer_or_payer: Optional[str] = None
    employee_or_payee: Optional[str] = None
    tax_year: Optional[int] = None
    fields: List[ExtractedField] = []
    raw_ocr_text: Optional[str] = None


class ValidationIssue(BaseModel):
    severity: str  # "error" | "warning" | "info"
    field: Optional[str] = None
    message: str


class AgentReviewResult(BaseModel):
    document_id: str
    issues: List[ValidationIssue]
    summary: str
    anomalies_flagged: int
