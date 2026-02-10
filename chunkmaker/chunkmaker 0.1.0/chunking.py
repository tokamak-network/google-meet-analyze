from __future__ import annotations

import hashlib
import re
from typing import Iterable, List, Tuple

from .types import ChunkRecord, MeetingRecord


def normalize_text(text: str) -> str:
    text = text.lstrip("\ufeff")
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def paragraph_block_spans(text: str) -> List[Tuple[int, int]]:
    if not text:
        return []
    spans: List[Tuple[int, int]] = []
    start = 0
    for match in re.finditer(r"\n\s*\n+", text):
        end = match.start()
        if end > start:
            spans.append((start, end))
        start = match.end()
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def sentence_end_positions(text: str) -> List[int]:
    ends = []
    pattern = r"(?:[.!?]|다\.|요\.|함\.)(?=\s|$)"
    for match in re.finditer(pattern, text):
        ends.append(match.end())
    return ends


def split_block_into_spans(block_start: int, block_text: str, max_chars: int) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    if len(block_text) <= max_chars:
        return [(block_start, block_start + len(block_text))]

    ends = sentence_end_positions(block_text)
    if not ends:
        for i in range(0, len(block_text), max_chars):
            spans.append((block_start + i, block_start + min(i + max_chars, len(block_text))))
        return spans

    current_start = 0
    last_end = 0
    for end in ends:
        if end - current_start <= max_chars:
            last_end = end
            continue

        if last_end == current_start:
            hard_end = min(current_start + max_chars, len(block_text))
            spans.append((block_start + current_start, block_start + hard_end))
            current_start = hard_end
            last_end = current_start
        else:
            spans.append((block_start + current_start, block_start + last_end))
            current_start = last_end
            last_end = current_start

        if end - current_start <= max_chars:
            last_end = end

    if current_start < len(block_text):
        if last_end > current_start:
            spans.append((block_start + current_start, block_start + last_end))
            current_start = last_end
        if current_start < len(block_text):
            for i in range(current_start, len(block_text), max_chars):
                spans.append((block_start + i, block_start + min(i + max_chars, len(block_text))))
    return spans


def merge_small_spans(spans: List[Tuple[int, int]], max_chars: int) -> List[Tuple[int, int]]:
    if not spans:
        return []
    merged: List[Tuple[int, int]] = []
    current_start, current_end = spans[0]
    for start, end in spans[1:]:
        if end - current_start <= max_chars:
            current_end = end
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    merged.append((current_start, current_end))
    return merged


def build_base_spans(text: str, max_chars: int) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    blocks = paragraph_block_spans(text)
    current_start: int | None = None
    current_end: int | None = None

    for block_start, block_end in blocks:
        block_len = block_end - block_start
        if current_start is None:
            if block_len <= max_chars:
                current_start, current_end = block_start, block_end
            else:
                spans.extend(split_block_into_spans(block_start, text[block_start:block_end], max_chars))
            continue

        potential_end = block_end
        if current_start is not None and potential_end - current_start <= max_chars:
            current_end = potential_end
        else:
            if current_start is not None and current_end is not None:
                spans.append((current_start, current_end))
            current_start, current_end = None, None
            if block_len <= max_chars:
                current_start, current_end = block_start, block_end
            else:
                spans.extend(split_block_into_spans(block_start, text[block_start:block_end], max_chars))

    if current_start is not None and current_end is not None:
        spans.append((current_start, current_end))
    return spans


def apply_overlap(spans: List[Tuple[int, int]], overlap_chars: int) -> List[Tuple[int, int]]:
    if not spans or overlap_chars <= 0:
        return spans
    overlapped: List[Tuple[int, int]] = []
    prev_end = None
    for start, end in spans:
        if prev_end is None:
            overlapped.append((start, end))
        else:
            overlap_start = max(0, prev_end - overlap_chars)
            adjusted_start = min(overlap_start, start)
            overlapped.append((adjusted_start, end))
        prev_end = end
    return overlapped


def chunk_text_from_normalized(
    record: MeetingRecord,
    normalized: str,
    max_chars: int,
    overlap_chars: int,
) -> List[ChunkRecord]:
    if not normalized:
        return []
    base_spans = build_base_spans(normalized, max_chars)
    spans = apply_overlap(base_spans, overlap_chars)

    chunks: List[ChunkRecord] = []
    for idx, (start, end) in enumerate(spans):
        text_slice = normalized[start:end]
        chunk_id = stable_chunk_id(record.meeting_key, idx, text_slice)
        chunks.append(
            ChunkRecord(
                meeting_key=record.meeting_key,
                date_ymd=record.date_ymd,
                meeting_name=record.meeting_name,
                chunk_index=idx,
                chunk_id=chunk_id,
                char_start=start,
                char_end=end,
                text=text_slice,
            )
        )
    return chunks


def chunk_text(record: MeetingRecord, max_chars: int, overlap_chars: int) -> List[ChunkRecord]:
    normalized = normalize_text(record.transcript)
    return chunk_text_from_normalized(record, normalized, max_chars, overlap_chars)


def stable_chunk_id(meeting_key: str, chunk_index: int, text_slice: str) -> str:
    payload = f"{meeting_key}|{chunk_index}|{text_slice}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def iter_chunk_records(
    records: Iterable[MeetingRecord],
    max_chars: int,
    overlap_chars: int,
) -> Iterable[ChunkRecord]:
    for record in records:
        for chunk in chunk_text(record, max_chars, overlap_chars):
            yield chunk
