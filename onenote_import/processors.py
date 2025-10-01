"""Utilities for cleaning OneNote HTML and preparing text files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List

from bs4 import BeautifulSoup

INVALID_FILENAME_CHARS = re.compile(r"[^\w\-]+", re.UNICODE)


def slugify(value: str, fallback: str = "section") -> str:
    value = value.strip().lower().replace(" ", "-")
    value = INVALID_FILENAME_CHARS.sub("-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or fallback


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts and styles for clarity
    for tag in soup(["script", "style"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)


def write_text_file(directory: Path, filename: str, content: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    output_path = directory / f"{filename}.txt"
    output_path.write_text(content, encoding="utf-8")
    return output_path


__all__ = ["slugify", "html_to_text", "write_text_file"]
