"""
Multi-step agent: validate -> flag anomalies -> draft summary.

This runs AFTER extraction (services/structurer.py already produced an
ExtractedDocument). The agent:
  1. Runs deterministic rule checks (cheap, fast, no LLM needed)
  2. Pulls relevant IRS guidance from the RAG store for any flagged field
  3. Asks Claude to draft a plain-English summary + recommendation, citing
     the retrieved guidance, for the human reviewer
"""
import os
import re
import anthropic

from app.models.schemas import ExtractedDocument, ValidationIssue, AgentReviewResult
from app.rag.store import query_knowledge

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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
                message=f"Low OCR confidence ({f.confidence:.0%}) for '{f.box_label}' = '{f.value}'. Please verify against source image.",
            ))

    # SSN/EIN format check
    for f in doc.fields:
        if "ssn" in f.box_label.lower() or "social security" in f.box_label.lower():
            if not SSN_RE.match(f.value.strip()):
                issues.append(ValidationIssue(
                    severity="error", field=f.box_label,
                    message=f"'{f.value}' does not match expected SSN format XXX-XX-XXXX.",
                ))
        if "ein" in f.box_label.lower() or "employer id" in f.box_label.lower():
            if not EIN_RE.match(f.value.strip()):
                issues.append(ValidationIssue(
                    severity="error", field=f.box_label,
                    message=f"'{f.value}' does not match expected EIN format XX-XXXXXXX.",
                ))

    # Box 1 vs Box 3 sanity check (W-2 specific)
    if doc.doc_type == "W-2":
        box1 = _field_value(doc, "box 1")
        box3 = _field_value(doc, "box 3")
        try:
            if box1 and box3:
                b1, b3 = float(box1.replace(",", "").replace("$", "")), float(box3.replace(",", "").replace("$", ""))
                if b1 > b3 * 1.05:  # allow small tolerance
                    issues.append(ValidationIssue(
                        severity="warning", field="Box 1 / Box 3",
                        message=f"Box 1 (${b1:,.2f}) is higher than Box 3 (${b3:,.2f}) by more than expected. Possible OCR misread.",
                    ))
        except ValueError:
            pass

    if not issues:
        issues.append(ValidationIssue(severity="info", message="No issues detected by rule checks."))

    return issues


def draft_summary(doc: ExtractedDocument, issues: list[ValidationIssue]) -> str:
    # pull relevant guidance for anything flagged
    flagged_terms = [i.field for i in issues if i.field and i.severity in ("warning", "error")]
    guidance_snippets = []
    for term in flagged_terms[:3]:
        hits = query_knowledge(term, n_results=1)
        guidance_snippets.extend(hits)

    guidance_text = "\n".join(f"- ({g['source']}) {g['text']}" for g in guidance_snippets) or "None retrieved."

    issues_text = "\n".join(f"- [{i.severity.upper()}] {i.field or 'general'}: {i.message}" for i in issues)

    prompt = f"""Document type: {doc.doc_type}
Extracted fields: {[(f.box_label, f.value) for f in doc.fields]}

Rule-check issues found:
{issues_text}

Relevant IRS guidance retrieved:
{guidance_text}

Write a short (3-5 sentence) plain-English summary for a human tax preparer
reviewing this document, calling out anything that needs their attention
before submission. Be concrete and specific, not generic."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


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
