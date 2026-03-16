"""File import module for various file formats."""

import os
import mimetypes
from pathlib import Path

import cv2
import pytesseract


def import_file(file_path):
    """Import and extract text from various file formats.
    
    Supported formats:
    - Text files (.txt)
    - PDF files (.pdf)
    - Image files (.png, .jpg, .jpeg)
    - Word documents (.docx)
    
    Args:
        file_path: Path to the file to import
        
    Returns:
        Extracted text as string
        
    Raises:
        Exception: If file format is unsupported or import fails
    """
    if not os.path.exists(file_path):
        raise Exception(f"File not found: {file_path}")
    
    file_path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(str(file_path))
    
    if mime_type == "text/plain" or file_path.suffix.lower() == ".txt":
        return import_text_file(file_path)
    elif mime_type == "application/pdf" or file_path.suffix.lower() == ".pdf":
        return import_pdf_file(file_path)
    elif mime_type in ["image/png", "image/jpeg"] or file_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
        return import_image_file(file_path)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_path.suffix.lower() == ".docx":
        return import_docx_file(file_path)
    else:
        raise Exception(f"Unsupported file format: {mime_type or 'unknown'}")


def import_text_file(file_path):
    """Import plain text file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read().strip()


def import_pdf_file(file_path):
    """Import PDF file using pypdf/pdfplumber."""
    try:
        # Try pdfplumber first (better text extraction)
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return '\n\n'.join(text_parts).strip()
    except ImportError:
        pass
    
    try:
        # Fallback to pypdf
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return '\n\n'.join(text_parts).strip()
    except ImportError:
        pass
    
    try:
        # Fallback to PyPDF2
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return '\n\n'.join(text_parts).strip()
    except ImportError:
        raise Exception("No PDF library available. Install pdfplumber, pypdf, or PyPDF2.")


def import_image_file(file_path):
    """Import image file using OCR."""
    img = cv2.imread(str(file_path))
    if img is None:
        raise Exception("Could not load image file")
    
    # Preprocess for better OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    processed = cv2.medianBlur(processed, 3)
    
    # Run OCR with Swedish and English
    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(processed, lang="swe+eng", config=custom_config)
    return text.strip()


def import_docx_file(file_path):
    """Import Word document (.docx)."""
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        return '\n\n'.join(text_parts).strip()
    except ImportError:
        raise Exception("python-docx library not available. Install with: pip install python-docx")