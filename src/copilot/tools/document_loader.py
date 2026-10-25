"""Load resume / document text from PDF, Markdown or plain-text files."""

import io
import re
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md"}


class DocumentLoadError(ValueError):
    """Raised when a document cannot be read or contains no extractable text."""


def clean_text(text: str) -> str:
    """Normalise whitespace while keeping line structure (bullets matter for resumes)."""
    text = text.replace("\x00", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def extract_pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as exc:
        raise DocumentLoadError(f"Not a readable PDF: {exc}") from exc
    return "\n\n".join(pages)


def load_document(source: str | Path | bytes, *, filename: str | None = None) -> str:
    """Return cleaned text from a file path, or raw bytes plus their filename (uploads)."""
    if isinstance(source, bytes):
        if filename is None:
            raise DocumentLoadError("filename is required when loading from bytes")
        data, suffix = source, Path(filename).suffix.lower()
    else:
        path = Path(source)
        data, suffix = path.read_bytes(), path.suffix.lower()

    if suffix not in SUPPORTED_SUFFIXES:
        raise DocumentLoadError(f"Unsupported file type '{suffix}'; use PDF, TXT or MD")

    raw = extract_pdf_text(data) if suffix == ".pdf" else data.decode("utf-8", errors="replace")
    text = clean_text(raw)
    if not text:
        # Usually a scanned/image-only PDF; OCR is out of scope for now.
        raise DocumentLoadError("No extractable text found (is the PDF a scanned image?)")
    return text
