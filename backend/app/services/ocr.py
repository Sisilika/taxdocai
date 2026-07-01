"""
OCR extraction service using Tesseract (free, open-source).

Pipeline:
  1. PDF -> images (pdf2image, needs poppler) OR accept image directly
  2. Tesseract OCR -> raw text + word-level bounding boxes
  3. Pass raw text to the structuring service (services/structurer.py) which
     uses Claude (cheap, fast model) with function-calling/tool-use to turn
     unstructured OCR text into the ExtractedDocument schema.

Note: Tesseract accuracy on real scanned W-2s/1099s is mediocre, especially
with skew or low-res scans. For production, swap this module for a vision-LLM
based extractor (see services/vision_extractor.py for the alternate path) --
the rest of the pipeline (structuring, validation, RAG) is unchanged either way.
"""
import io
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes


def ocr_image(image_bytes: bytes) -> dict:
    """Run Tesseract on a single image, return text + word-level boxes."""
    img = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(img)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    words = []
    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        if not word:
            continue
        words.append({
            "text": word,
            "bbox": [
                data["left"][i],
                data["top"][i],
                data["left"][i] + data["width"][i],
                data["top"][i] + data["height"][i],
            ],
            "conf": float(data["conf"][i]) / 100.0 if data["conf"][i] != "-1" else 0.0,
        })
    return {"text": text, "words": words}


def ocr_file(filename: str, file_bytes: bytes) -> dict:
    """Entry point: handles both PDF and image uploads."""
    if filename.lower().endswith(".pdf"):
        pages = convert_from_bytes(file_bytes, dpi=300)
        full_text = []
        all_words = []
        for page in pages:
            buf = io.BytesIO()
            page.save(buf, format="PNG")
            result = ocr_image(buf.getvalue())
            full_text.append(result["text"])
            all_words.extend(result["words"])
        return {"text": "\n".join(full_text), "words": all_words}
    else:
        return ocr_image(file_bytes)
