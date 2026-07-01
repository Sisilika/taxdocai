"""
Multi-step agent: validate -> flag anomalies -> draft summary.

Runs AFTER extraction. Steps:
  1. Deterministic rule checks (no LLM needed)
  2. RAG lookup for any flagged field against IRS instruction chunks
  3. Groq (free) drafts a plain-English summary citing retrieved guidance

Free model: llama-3.3-70b-versatile via Groq.
"""
import os
import re
from groq import Groq

from app.models.schemas import ExtractedDocument, ValidationIssue, AgentReviewResult
from app.rag.store import query_knowledge

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SSN_RE = re.compile(r"^\d{3}-\d{2}-\d{4}$")
EIN_RE = re.compile(r"^\d{2}-\d{7}$")


def _field_value(doc: ExtractedDocument, label_substr: str) -> str | None:
    for f in doc.fields:
        if label_substr.lower() in f.box_label.lower():
            return f.value
    return None


def run_rule_checks(doc: ExtractedDocument) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    # Low-confidence OCR fields
    for f in doc.fields:
        if f.confidence < 0.6:
            issues.append(ValidationIssue(
                severity="warning",
                field=f.box_label,
                message=(
                    f"Low OCR confidence ({f.confidence:.0%}) for '{f.box_label}'"
                    f" = '{f.value}'. Please verify against source image."
                ),
            ))

    # SSN / EIN format checks
    for f in doc.fields:
        if "ssn" in f.box_label.lower() or "social security" in f.box_label.lower():
            if not SSN_RE.match(f.value.strip()):
                issues.append(ValidationIssue(
                    severity="error",
                    field=f.box_label,
                    message=f"'{f.value}' does not match expected SSN format XXX-XX-XXXX.",
                ))
        if "ein" in f.box_label.lower() or "employer id" in f.box_label.lower():
            if not EIN_RE.match(f.value.strip()):
                issues.append(ValidationIssue(
                    severity="error",
                    field=f.box_label,
                    message=f"'{f.value}' does not match expected EIN format XX-XXXXXXX.",
                ))

    # W-2 Box 1 vs Box 3 sanity check
    if doc.doc_type == "W-2":
        box1 = _field_value(doc, "box 1")
        box3 = _field_value(doc, "box 3")
        try:
            if box1 and box3:
                b1 = float(box1.replace(",", "").replace("$", ""))
                b3 = float(box3.replace(",", "").replace("$", ""))
                if b1 > b3 * 1.05:
                    issues.append(ValidationIssue(
                        severity="warning",
                        field="Box 1 / Box 3",
                        message=(
                            f"Box 1 (${b1:,.2f}) exceeds Box 3 (${b3:,.2f}) by more"
                            " than expected — possible OCR misread."
                        ),
                    ))
        except ValueError:
            pass

    if not issues:
        issues.append(ValidationIssue(severity="info", message="No issues detected by rule checks."))

    return issues


def draft_summary(doc: ExtractedDocument, issues: list[ValidationIssue]) -> str:
    flagged = [i.field for i in issues if i.field and i.severity in ("warning", "error")]
    guidance_snippets = []
    for term in flagged[:3]:
        hits = query_knowledge(term, n_results=1)
        guidance_snippets.extend(hits)

    guidance_text = (
        "\n".join(f"- ({g['source']}) {g['text']}" for g in guidance_snippets)
        or "None retrieved."
    )
    issues_text = "\n".join(
        f"- [{i.severity.upper()}] {i.field or 'general'}: {i.message}" for i in issues
    )

    prompt = f"""Document type: {doc.doc_type}
Extracted fields: {[(f.box_label, f.value) for f in doc.fields]}

Rule-check issues:
{issues_text}

Relevant IRS guidance:
{guidance_text}

Write a 3-5 sentence plain-English summary for a human tax preparer reviewing
this document, calling out anything needing attention before submission.
Be specific and concrete, not generic."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    return response.choices[0].message.content.strip()


def run_agent(doc: ExtractedDocument) -> AgentReviewResult:
    issues = run_rule_checks(doc)
    summary = draft_summary(doc, issues)
    anomalies = sum(1 for i in issues if i.severity in ("warning", "error"))
    return AgentReviewResult(
        document_id=doc.document_id,
        issues=issues,
        summary=summary,
        anomalies_flagged=anomalies,
    )
