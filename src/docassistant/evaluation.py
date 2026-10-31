"""Evaluation logic.

Pure functions on plain data (no Azure calls), so they can be unit-tested offline.
A "source" is a (file name, page) tuple.
"""
import re
from collections import defaultdict

Source = tuple[str, int]

_CITATION = re.compile(r"([\w.\-]+\.pdf)\s*,\s*p\.?\s*(\d+)", re.IGNORECASE)

JUDGE_SYSTEM_PROMPT = (
    "Tu es un correcteur strict. On te donne une question, la réponse attendue (points clés) "
    "et la réponse d'un assistant. Réponds OUI uniquement si la réponse de l'assistant contient "
    "tous les éléments de la réponse attendue et n'affirme rien qui la contredise. "
    "Sinon réponds NON. Réponds par un seul mot : OUI ou NON."
)


def as_sources(items) -> list[Source]:
    """Convert [[file, page], ...] (as read from JSON) to a list of tuples."""
    return [(name, int(page)) for name, page in items]


def parse_citations(text: str) -> set[Source]:
    """Extract every (file, page) cited in an answer, e.g. [doc.pdf, p. 24]."""
    return {(name, int(page)) for name, page in _CITATION.findall(text)}


def is_refusal(text: str, not_found: str) -> bool:
    """True if the answer is the standard refusal sentence (quotes and final period ignored)."""
    def clean(s: str) -> str:
        return s.strip().strip("«»\"' \n").rstrip(".").strip().lower()
    return clean(text) == clean(not_found)


def hit(expected: list[Source], retrieved: list[Source]) -> bool:
    """True if at least one expected page is among the retrieved passages."""
    return bool(set(expected) & set(retrieved))


def first_rank(expected: list[Source], retrieved: list[Source]) -> int | None:
    """Rank (1-based) of the first retrieved passage that is an expected page, or None."""
    wanted = set(expected)
    for rank, source in enumerate(retrieved, start=1):
        if source in wanted:
            return rank
    return None


def recall(expected: list[Source], retrieved: list[Source]) -> float:
    """Share of the expected pages that were retrieved."""
    if not expected:
        return 1.0
    got = set(retrieved)
    return sum(1 for s in expected if s in got) / len(expected)


def judge_messages(question: str, expected_answer: str, answer_text: str) -> list[dict]:
    return [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Question : {question}\n"
                f"Réponse attendue : {expected_answer}\n"
                f"Réponse de l'assistant : {answer_text}"
            ),
        },
    ]


def parse_verdict(text: str) -> bool:
    return text.strip().upper().startswith("OUI")


def summarize(results: list[dict], modes: tuple[str, ...]) -> dict:
    """Aggregate per-question results.

    Each result has: category, behavior ("answer" | "refuse"), hit {mode: bool},
    recall {mode: float}, rank {mode: int | None}, refused, correct, cited_expected,
    citations_valid.
    """
    answerable = [r for r in results if r["behavior"] == "answer"]
    refusals = [r for r in results if r["behavior"] == "refuse"]

    by_category = defaultdict(list)
    for r in answerable:
        by_category[r["category"]].append(r)

    return {
        "n_answerable": len(answerable),
        "n_refusals": len(refusals),
        "retrieval_hit": {m: sum(1 for r in answerable if r["hit"][m]) for m in modes},
        "retrieval_hit_at_1": {m: sum(1 for r in answerable if r["rank"][m] == 1) for m in modes},
        "retrieval_mrr": {
            m: sum(1 / r["rank"][m] if r["rank"][m] else 0.0 for r in answerable) / len(answerable)
            if answerable else 0.0
            for m in modes
        },
        "retrieval_recall": {
            m: sum(r["recall"][m] for r in answerable) / len(answerable) if answerable else 0.0
            for m in modes
        },
        "retrieval_hit_by_category": {
            cat: {"n": len(items), **{m: sum(1 for r in items if r["hit"][m]) for m in modes}}
            for cat, items in sorted(by_category.items())
        },
        "correct": sum(1 for r in answerable if r["correct"]),
        "false_refusals": sum(1 for r in answerable if r["refused"]),
        "cited_expected": sum(1 for r in answerable if r["cited_expected"]),
        "correct_refusals": sum(1 for r in refusals if r["refused"]),
        "invalid_citations": sum(1 for r in results if not r["citations_valid"]),
    }
