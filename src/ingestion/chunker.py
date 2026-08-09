"""Structural chunker for extracted document text."""

import uuid
from typing import List, Dict, Any
from src.models.domain import TextChunk


def create_chunks_from_blocks(
    doc_id: str,
    doc_name: str,
    blocks: List[Dict[str, Any]],
    max_chunk_chars: int = 1500,
    min_chunk_chars: int = 100
) -> List[TextChunk]:
    """Convert parsed structural blocks into TextChunk items with exact position tracking."""
    chunks: List[TextChunk] = []
    current_char_offset = 0

    for idx, b in enumerate(blocks):
        text = b.get("text", "").strip()
        if not text:
            continue

        loc = b.get("location", f"Block {idx + 1}")
        title = b.get("title")

        # If a block is very large (e.g. a long page in PDF), split by paragraph
        if len(text) > max_chunk_chars:
            sub_paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
            sub_buffer = ""
            sub_start = current_char_offset

            for sub in sub_paragraphs:
                if len(sub_buffer) + len(sub) > max_chunk_chars and len(sub_buffer) >= min_chunk_chars:
                    end_offset = sub_start + len(sub_buffer)
                    chunks.append(TextChunk(
                        chunk_id=str(uuid.uuid4()),
                        doc_id=doc_id,
                        doc_name=doc_name,
                        section_title=title,
                        page_num=b.get("page_num"),
                        text=sub_buffer.strip(),
                        start_char=sub_start,
                        end_char=end_offset
                    ))
                    sub_start = end_offset + 1
                    sub_buffer = sub + "\n"
                else:
                    sub_buffer += sub + "\n"

            if sub_buffer.strip():
                end_offset = sub_start + len(sub_buffer)
                chunks.append(TextChunk(
                    chunk_id=str(uuid.uuid4()),
                    doc_id=doc_id,
                    doc_name=doc_name,
                    section_title=title,
                    page_num=b.get("page_num"),
                    text=sub_buffer.strip(),
                    start_char=sub_start,
                    end_char=end_offset
                ))
            current_char_offset += len(text) + 2

        else:
            end_offset = current_char_offset + len(text)
            chunks.append(TextChunk(
                chunk_id=str(uuid.uuid4()),
                doc_id=doc_id,
                doc_name=doc_name,
                section_title=title or loc,
                page_num=b.get("page_num"),
                text=text,
                start_char=current_char_offset,
                end_char=end_offset
            ))
            current_char_offset = end_offset + 2

    return chunks
