"""Query log: one JSON line per question or feedback, to follow cost, latency and quality."""
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "queries.jsonl"


def log_event(event: dict, path: Path = LOG_FILE) -> None:
    """Append one event (a dict) to the log, with a UTC timestamp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), **event}
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
