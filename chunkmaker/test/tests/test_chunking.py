from __future__ import annotations

import unittest

from chunkmaker.chunking import chunk_text_from_normalized, normalize_text, stable_chunk_id
from chunkmaker.types import MeetingRecord


class TestChunking(unittest.TestCase):
    def test_normalize_text_newlines(self):
        raw = "\ufeffLine1\\r\\nLine2\r\nLine3\rLine4\tTab\n\n\nLine5"
        normalized = normalize_text(raw)
        self.assertEqual(normalized, "Line1\nLine2\nLine3\nLine4 Tab\n\nLine5")

    def test_deterministic_chunk_boundaries(self):
        text = "Para1 line.\n\nPara2 line.\n\nPara3 line."
        record = MeetingRecord(
            meeting_key="abc",
            date_ymd="2026-02-02",
            meeting_name="Meeting",
            row_index=0,
            transcript=text,
        )
        normalized = normalize_text(text)
        chunks_a = chunk_text_from_normalized(record, normalized, 20, 0)
        chunks_b = chunk_text_from_normalized(record, normalized, 20, 0)
        self.assertEqual(
            [(c.char_start, c.char_end) for c in chunks_a],
            [(c.char_start, c.char_end) for c in chunks_b],
        )

    def test_stable_chunk_id(self):
        chunk_id_a = stable_chunk_id("abc", 0, "text")
        chunk_id_b = stable_chunk_id("abc", 0, "text")
        self.assertEqual(chunk_id_a, chunk_id_b)


if __name__ == "__main__":
    unittest.main()
