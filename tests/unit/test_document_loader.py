import io
from pathlib import Path

import pytest
from pypdf import PdfWriter

from copilot.tools.document_loader import DocumentLoadError, clean_text, load_document

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_clean_text_collapses_spaces_and_blank_lines() -> None:
    raw = "Jane   Doe\t\n\n\n\n- Built   things  \x00"
    assert clean_text(raw) == "Jane Doe\n\n- Built things"


def test_load_markdown_file() -> None:
    text = load_document(FIXTURES / "sample_resume.md")
    assert "Jane Doe" in text
    assert "Kafka" in text


def test_load_from_bytes_requires_filename() -> None:
    with pytest.raises(DocumentLoadError, match="filename"):
        load_document(b"hello")


def test_unsupported_suffix() -> None:
    with pytest.raises(DocumentLoadError, match="Unsupported"):
        load_document(b"data", filename="resume.docx")


def test_image_only_pdf_raises() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    with pytest.raises(DocumentLoadError, match="No extractable text"):
        load_document(buf.getvalue(), filename="scan.pdf")


def test_corrupt_pdf_raises() -> None:
    with pytest.raises(DocumentLoadError, match="readable PDF"):
        load_document(b"not a pdf at all", filename="resume.pdf")
