# verifier/ocr_verifier.py

import os
import logging
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define supporting document types and their keywords
SUPPORTING_DOCUMENT_TYPES = {
    'medical': {
        'keywords': ['diagnosis', 'prescription', 'treatment', 'hospital', 'doctor', 'medical'],
        'score_weight': 20
    },
    'education': {
        'keywords': ['fee', 'receipt', 'admission', 'university', 'college', 'semester'],
        'score_weight': 20
    },
    'ngo_certificate': {
        'keywords': ['registration', 'government', 'trust', 'society', 'certificate', 'NGO'],
        'score_weight': 20
    }
}

def is_pdf(file_path: str) -> bool:
    return file_path.lower().endswith('.pdf')

def extract_text(file_path: str) -> str:
    try:
        if is_pdf(file_path):
            logger.info("PDF detected. Converting to images for OCR...")
            pages = convert_from_path(file_path, dpi=300)
            full_text = ""
            for page in pages:
                full_text += pytesseract.image_to_string(page) + "\n"
            return full_text.lower()
        else:
            logger.info("Image detected. Using pytesseract directly.")
            return pytesseract.image_to_string(Image.open(file_path)).lower()
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""

def score_supporting_document(text: str, doc_type: str) -> int:
    if doc_type not in SUPPORTING_DOCUMENT_TYPES:
        logger.warning(f"Unknown supporting document type: {doc_type}")
        return 0

    keywords = SUPPORTING_DOCUMENT_TYPES[doc_type]['keywords']
    matched = [kw for kw in keywords if kw.lower() in text]
    score = int((len(matched) / len(keywords)) * SUPPORTING_DOCUMENT_TYPES[doc_type]['score_weight'])

    logger.info(f"Matched keywords: {matched}")
    logger.info(f"Score breakdown: {len(matched)}/{len(keywords)} keywords matched.")
    return score

def verify_supporting_document(path: str, doc_type: str = 'medical') -> int:
    """
    Verifies authenticity of a supporting document (image or PDF) based on
    OCR-extracted text and keyword matching.

    Args:
        path (str): Path to the file (image or PDF)
        doc_type (str): Type of supporting document ('medical', 'education', etc.)

    Returns:
        int: Score out of 20
    """
    logger.info(f"Verifying supporting document: {path} as {doc_type}")

    if not os.path.exists(path):
        logger.warning("Document not found.")
        return 0

    text = extract_text(path)
    if not text:
        logger.warning("No text extracted from document.")
        return 0

    score = score_supporting_document(text, doc_type)
    logger.info(f"Supporting document score for '{doc_type}': {score}/20")
    return score
