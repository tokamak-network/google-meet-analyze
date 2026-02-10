from __future__ import annotations

import csv
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .types import MeetingRecord


csv.field_size_limit(sys.maxsize)


def discover_csv_files(input_path: Optional[str] = None) -> List[Path]:
    candidates: List[Path] = []
    if input_path:
        path = Path(input_path)
        if path.is_dir():
            candidates.extend(sorted(path.glob("*.csv")))
        elif path.is_file():
            candidates.append(path)
    else:
        for base in [Path.cwd(), Path.cwd() / "data"]:
            if base.exists() and base.is_dir():
                candidates.extend(sorted(base.glob("*.csv")))

    unique = []
    seen = set()
    for item in candidates:
        if item.resolve() in seen:
            continue
        seen.add(item.resolve())
        unique.append(item)
    return unique


def has_transcript_columns(fieldnames: Optional[Sequence[str]]) -> bool:
    if not fieldnames:
        return False
    fields = {f.strip() for f in fieldnames if f}
    return "content" in fields or "content_clean" in fields


def select_transcript(row: dict) -> str:
    content_clean = row.get("content_clean")
    if content_clean:
        return content_clean
    content = row.get("content")
    return content or ""


def extract_date_ymd(row: dict, meeting_name: str) -> str:
    date_fields = [
        "date_ymd",
        "date",
        "createdTime",
        "created_time",
        "created_at",
        "start_time",
        "startTime",
        "meeting_date",
    ]

    for key in date_fields:
        value = row.get(key)
        if value:
            date_val = normalize_date_string(value)
            if date_val:
                return date_val

    date_from_name = normalize_date_string(meeting_name)
    if date_from_name:
        return date_from_name
    return ""


def normalize_date_string(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    value = value[:50]
    match = re.search(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", value)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    match = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", value)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    if len(value) >= 10 and value[4] == "-" and value[7] == "-":
        return value[:10]
    return ""


def compute_meeting_key(row: dict, meeting_name: str, date_ymd: str, row_index: int) -> str:
    if row.get("meeting_key"):
        return str(row.get("meeting_key"))
    payload = f"{meeting_name}|{date_ymd}|{row_index}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:12]


def iter_meeting_records(paths: Iterable[Path]) -> Iterable[MeetingRecord]:
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not has_transcript_columns(reader.fieldnames):
                continue
            for row_index, row in enumerate(reader):
                meeting_name = (row.get("name") or "").strip()
                transcript = select_transcript(row)
                if not transcript:
                    continue
                date_ymd = extract_date_ymd(row, meeting_name)
                meeting_key = compute_meeting_key(row, meeting_name, date_ymd, row_index)
                yield MeetingRecord(
                    meeting_key=meeting_key,
                    date_ymd=date_ymd,
                    meeting_name=meeting_name,
                    row_index=row_index,
                    transcript=transcript,
                    source_file=str(path),
                )
