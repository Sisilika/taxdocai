"""
Mock integration connector: exports reviewed documents to a standard
tax-prep CSV/XML shape. Real Drake/UltraTax APIs aren't publicly available,
so this stub demonstrates the mapping layer -- see /docs/INTEGRATION.md for
notes on how this would map to a real product's import format.
"""
import csv
import io
import xml.etree.ElementTree as ET
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.routers.documents import _DOCS

router = APIRouter()


@router.get("/csv/{document_id}")
def export_csv(document_id: str):
    doc = _DOCS.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["DocType", "TaxYear", "PayerOrEmployer", "PayeeOrEmployee", "BoxLabel", "Value", "Confidence"])
    for f in doc.fields:
        writer.writerow([doc.doc_type, doc.tax_year, doc.employer_or_payer, doc.employee_or_payee, f.box_label, f.value, f.confidence])
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={document_id}.csv"},
    )


@router.get("/xml/{document_id}")
def export_xml(document_id: str):
    doc = _DOCS.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    root = ET.Element("TaxDocument")
    ET.SubElement(root, "DocType").text = doc.doc_type
    ET.SubElement(root, "TaxYear").text = str(doc.tax_year or "")
    ET.SubElement(root, "PayerOrEmployer").text = doc.employer_or_payer or ""
    ET.SubElement(root, "PayeeOrEmployee").text = doc.employee_or_payee or ""
    fields_el = ET.SubElement(root, "Fields")
    for f in doc.fields:
        field_el = ET.SubElement(fields_el, "Field")
        ET.SubElement(field_el, "BoxLabel").text = f.box_label
        ET.SubElement(field_el, "Value").text = f.value
        ET.SubElement(field_el, "Confidence").text = str(f.confidence)

    xml_bytes = io.BytesIO()
    ET.ElementTree(root).write(xml_bytes, encoding="utf-8", xml_declaration=True)
    xml_bytes.seek(0)

    return StreamingResponse(
        iter([xml_bytes.getvalue()]),
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={document_id}.xml"},
    )
