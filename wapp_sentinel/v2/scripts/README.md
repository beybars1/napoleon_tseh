# Timestamp verification script

This script samples recent rows and checks whether timestamp columns are UTC-aware (`timestamptz`).

## Usage

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/napoleon-sentinel-db"
python /home/beybars/Desktop/beybars/projects/napoleon_tseh/wapp_sentinel/v2/scripts/verify_timestamps.py
```

## Output meanings

- `UTC` → aware datetime with UTC offset
- `naive` → datetime without timezone info
- `NULL` → no value
- `offset_+N` / `offset_-N` → aware but not UTC (unexpected)
