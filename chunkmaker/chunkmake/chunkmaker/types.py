from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MeetingRecord:
    meeting_key: str
    date_ymd: str
    meeting_name: str
    row_index: int
    transcript: str
    source_file: str | None = None


@dataclass
class ChunkRecord:
    meeting_key: str
    date_ymd: str
    meeting_name: str
    chunk_index: int
    chunk_id: str
    char_start: int
    char_end: int
    text: str


@dataclass
class MeetingMeta:
    meeting_key: str
    date_ymd: str
    meeting_name: str
    transcript_char_len: int
    chunk_count: int
    source_file: Optional[str] = None
