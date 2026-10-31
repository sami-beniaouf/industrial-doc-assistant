"""Ask a question to the assistant, or run a set of test questions.

Run from the repository root:
    python scripts/ask.py "Quelle norme s'applique aux machines à meuler fixes ?"
    python scripts/ask.py                      (runs the built-in test questions)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docassistant.answer import answer  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

TEST_QUESTIONS = [
    "Quelles sont les règles de sécurité pour la meuleuse d'angle ?",
    "Quelle norme s'applique aux machines à meuler fixes ?",
    "La norme EN ISO 16090–1 donne-t-elle une présomption de conformité ?",
    "Faut-il porter des gants sur une fraiseuse conventionnelle ?",
    "Quelle est la température de fusion de l'aluminium ?",
]

questions = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else TEST_QUESTIONS

for question in questions:
    result = answer(question)
    print("=" * 100)
    print(f"Q: {question}\n")
    print(f"R: {result.text}\n")
    print("Retrieved passages:")
    for rank, p in enumerate(result.passages, start=1):
        print(f"  {rank}. {p.source} p.{p.page}")
    print(f"({result.total_tokens} tokens)")
