"""Load and chunk a manuscript file for processing."""
from __future__ import annotations

import re
from pathlib import Path

import structlog

from cati.manuscript_review.models import ManuscriptChunk

log = structlog.get_logger(__name__)

# Target chunk size in words — keeps each chunk within context window limits.
DEFAULT_CHUNK_SIZE = 15_000

# Patterns that indicate chapter boundaries (Danish).
_CHAPTER_PATTERNS = [
    re.compile(r"^#+\s+", re.MULTILINE),  # Markdown headers
    re.compile(r"^Kapitel\s+\d+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Prolog\b", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Epilog\b", re.MULTILINE | re.IGNORECASE),
]


def _detect_chapters(text: str) -> list[tuple[str, str]]:
    """Split text into (chapter_title, chapter_content) pairs.

    Uses markdown headers or 'Kapitel N' patterns. Falls back to
    splitting by word count if no chapter boundaries are found.
    """
    # Try markdown headers first (# Title)
    header_pattern = re.compile(r"^(#+\s+.+)$", re.MULTILINE)
    headers = list(header_pattern.finditer(text))

    if len(headers) >= 2:
        chapters: list[tuple[str, str]] = []
        for i, match in enumerate(headers):
            title = match.group(1).strip().lstrip("#").strip()
            start = match.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            content = text[start:end].strip()
            if content:
                chapters.append((title, content))
        return chapters

    # Try 'Kapitel N' pattern
    kapitel_pattern = re.compile(
        r"^((?:Prolog|Epilog|Kapitel\s+\d+[^:\n]*))", re.MULTILINE | re.IGNORECASE
    )
    matches = list(kapitel_pattern.finditer(text))

    if len(matches) >= 2:
        chapters = []
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            if content:
                chapters.append((title, content))
        return chapters

    # Fallback: treat entire text as one chapter
    return [("Hele manuskriptet", text)]


def _chunk_text(text: str, max_words: int) -> list[str]:
    """Split text into chunks of approximately *max_words* words.

    Tries to split at paragraph boundaries to avoid cutting mid-sentence.
    """
    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks: list[str] = []
    paragraphs = text.split("\n\n")
    current_chunk: list[str] = []
    current_words = 0

    for para in paragraphs:
        para_words = len(para.split())
        if current_words + para_words > max_words and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_words = para_words
        else:
            current_chunk.append(para)
            current_words += para_words

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def load_manuscript(
    path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> list[ManuscriptChunk]:
    """Load a manuscript file and split it into processable chunks.

    Supports plain text (.txt) and markdown (.md) files.
    The manuscript is first split by chapters, then each chapter
    is further chunked if it exceeds *chunk_size* words.

    Returns a flat list of ManuscriptChunk objects ready for agent processing.
    """
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"Manuscript not found: {filepath}")

    text = filepath.read_text(encoding="utf-8")
    log.info("manuscript_loaded", path=str(filepath), total_words=len(text.split()))

    chapters = _detect_chapters(text)
    all_chunks: list[ManuscriptChunk] = []

    for chapter_title, chapter_content in chapters:
        sub_chunks = _chunk_text(chapter_content, chunk_size)
        for i, chunk_text in enumerate(sub_chunks):
            all_chunks.append(
                ManuscriptChunk(
                    chapter=chapter_title,
                    content=chunk_text,
                    word_count=len(chunk_text.split()),
                    chunk_index=i,
                    total_chunks=len(sub_chunks),
                )
            )

    log.info(
        "manuscript_chunked",
        chapters=len(chapters),
        total_chunks=len(all_chunks),
        total_words=sum(c.word_count for c in all_chunks),
    )
    return all_chunks
