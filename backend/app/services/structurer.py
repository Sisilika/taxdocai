"""
Structuring service: raw OCR text -> structured ExtractedDocument.

Uses Groq (free tier) with tool-use/function-calling so the model is forced
to return data in the exact schema shape.

Free model used: llama-3.3-70b-versatile (best Groq model for tool-calling)
Get a free API key at: https://console.groq.com
"""
import os
import json
import uuid
from groq import Groq

from app.models.schemas import ExtractedDocument, ExtractedField, DocType

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"

EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "record_tax_document",
        "description": "Record structured fields extracted from a tax document (W-2, 1099, K-1, etc).",
        "parameters": {
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
                            "box_label": {
                                "type": "string",
                                "description": "e.g. 'Box 1 - Wages'",
                            },
                            "value": {"type": "string"},
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                        "required": ["box_label", "value", "confidence"],
                    },
                },
            },
            "required": ["doc_type", "fields"],
        },
    },
}

SYSTEM_PROMPT = """You are a tax document structuring engine. You will be given raw,
noisy OCR text from a scanned tax document (W-2, 1099 variant, or K-1). Identify the
document type and extract every labeled box/field you can find using the
record_tax_document tool. If OCR text is garbled for a field, still report your best
guess and lower its confidence score accordingly. Never invent values not present in the
text. Always call the tool — do not respond with plain text."""


def structure_document(ocr_text: str) -> ExtractedDocument:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Raw OCR text:\n\n{ocr_text}"},
        ],
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "function", "function": {"name": "record_tax_document"}},
        max_tokens=2000,
    )

    tool_call = response.choices[0].message.tool_calls[0]
    data = json.loads(tool_call.function.arguments)

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
