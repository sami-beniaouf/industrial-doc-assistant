"""Third test: run the same questions in keyword, vector and hybrid mode and compare.

Run from the repository root:  python scripts/check_search.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docassistant.search import MODES, retrieve  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

QUESTIONS = [
    "Quelle norme s'applique aux machines à meuler fixes ?",
    "Quelle norme encadre les meuleuses fixes ?",
    "EN ISO 16089",
    "Comment se protéger des projections lors du meulage ?",
]

for question in QUESTIONS:
    print("=" * 100)
    print(question)
    for mode in MODES:
        print(f"\n--- {mode}")
        for rank, p in enumerate(retrieve(question, top=5, mode=mode), start=1):
            snippet = p.content[:90].replace("\n", " ")
            print(f"{rank}. score={p.score:.4f}  {p.source} p.{p.page}  | {snippet}...")
