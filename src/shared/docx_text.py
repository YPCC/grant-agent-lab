"""Extract plain text from a .docx without requiring python-docx at import time."""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def extract_text(path: str | Path) -> str:
    p = Path(path)
    try:
        from docx import Document  # type: ignore

        doc = Document(p)
        parts = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        if parts:
            return "\n\n".join(parts)
    except Exception:
        pass
    with ZipFile(p) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    chunks: list[str] = []
    for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
        if node.text:
            chunks.append(node.text)
    return "\n".join(chunks)
