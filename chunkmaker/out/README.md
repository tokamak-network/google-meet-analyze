# ChunkMaker Output

Generated artifacts from `python -m chunkmaker run`.

## Files
- `chunks.jsonl`: chunk records, one JSON per line
- `chunks.tsv`: tab-separated export for quick inspection
- `meetings.jsonl`: meeting-level metadata

## Format Notes
- `chunk_id` is stable for the same input and parameters.
- `char_start`/`char_end` offsets refer to the normalized transcript text.
- TSV uses literal `\n` for newlines inside the chunk text.
