"""Run the ingestion from the repository root:  python scripts/ingest.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docassistant.ingest import main  # noqa: E402

main()
