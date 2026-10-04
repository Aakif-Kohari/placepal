"""Resume text extraction. PDFs are parsed locally with pypdf."""
from __future__ import annotations

import re
from typing import BinaryIO

MIN_RESUME_CHARS = 80


def clean_text(text: str) -> str:
    """Collapse noisy whitespace that PDF extraction tends to produce."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(file: BinaryIO) -> str:
    """Read all pages of a PDF and return cleaned text."""
    from pypdf import PdfReader

    reader = PdfReader(file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return clean_text("\n".join(pages))


def is_usable(text: str) -> bool:
    """A resume with almost no text (e.g. a scanned image) cannot be used."""
    return len(text.strip()) >= MIN_RESUME_CHARS
