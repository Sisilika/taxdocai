"""
Structuring service: raw OCR text -> structured ExtractedDocument.

Uses Claude with tool-use/function-calling so the model is forced to return
data in the exact schema shape rather than free-text JSON it might botch.
This is the "structured JSON extraction using Claude with function calling"
piece of the pipeline.
"""
import os
import json
import uuid
import anthropic

from app.models.schemas import ExtractedDocument, ExtractedField, DocType

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

EXTRACTION_TOOL = {
    "name": "record_tax_document",
    "description": "Record structured fields extracted from a tax document (W-2, 1099, K-1, etc).",
    "input_schema": {
        "type": "object",
        "properties": {
            "doc_type": {
                "type": "string",
                "enum": ["W-2", "1099-NEC", "1099-INT", "1099-DIV", "K-1", "UNKNOWN"],
            },
            "employer_or_payer": {"type": "string"},
            "employee_or_payee": {"type": "string"},
            "tax_year": {"type": "integer"},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "box_label": {"type": "string", "description": "e.g. 'Box 1 - Wages'"},
                        "value": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["box_label", "value", "confidence"],
                },
            },
        },
        "required": ["doc_type", "fields"],
    },
}

SYSTEM_PROMPT = """You are a tax document structuring engine. You will be given raw,
noisy OCR text from a scanned tax document (W-2, 1099 variant, or K-1). Identify the
document type and extract every labeled box/field you can find into the
record_tax_document tool. If OCR text is garbled for a field, still report your best
guess and lower its confidence score accordingly. Never invent values that aren't
present in the text."""


def structure_document(ocr_text: str) -> ExtractedDocument:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "record_tax_document"},
        messages=[
            {"role": "user", "content": f"Raw OCR text:\n\n{ocr_text}"}
        ],
    )

    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    data = tool_use_block.input

    fields = [ExtractedField(**f) for f in data.get("fields", [])]

    return ExtractedDocument(
        document_id=str(uuid.uuid4()),
        doc_type=DocType(data.get("doc_type", "UNKNOWN")),
        employer_or_payer=data.get("employer_or_payer"),
        employee_or_payee=data.get("employee_or_payee"),
        tax_year=data.get("tax_year"),
        fields=fields,
        raw_ocr_text=ocr_text,
    )
