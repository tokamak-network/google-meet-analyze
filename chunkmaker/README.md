# ChunkMaker v1

Local pipeline that reads ATI meeting transcript CSV exports and produces stable, deterministic chunks for downstream analysis and web UI rendering.

## Requirements
- Python 3.10+

## Installation
No external dependencies. Use the local package directly.

```bash
python3 -m chunkmaker --help
```

## Quick Start
```bash
python3 -m chunkmaker run --out out
```

Optional flags:
```bash
python3 -m chunkmaker run --input <path_or_dir> --out out --max-chars 2500 --overlap-chars 150 --strategy paragraphs
```

## How It Works
- Prefers `content_clean` if present, otherwise `content`.
- Normalizes line endings, tabs, and excessive blank lines.
- Splits by paragraph blocks, merges up to `max_chars`.
- If a block is too large, splits by sentence boundary, then hard-splits as fallback.
- Adds `overlap_chars` between consecutive chunks.
- Emits deterministic `chunk_id` values from meeting key, index, and slice text.

## Outputs
Written to `out/` (see `out/README.md` for format details):
- `chunks.jsonl` (one JSON per line)
- `chunks.tsv` (tab-separated)
- `meetings.jsonl` (meeting-level metadata)

## Testing
```bash
python3 -m unittest discover -s tests
```
