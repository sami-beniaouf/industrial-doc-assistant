"""Run the evaluation set (eval/questions.json) and write eval/results.json.

Run from the repository root:
    python scripts/evaluate.py             one run
    python scripts/evaluate.py --runs 3    repeat generation and judging 3 times (the model is not deterministic)
    python scripts/evaluate.py --questions eval/questions_holdout.json --out eval/results_holdout.json

For every question:
  - retrieval is run in the three modes (keyword, vector, hybrid) and compared with the expected pages;
  - the answer is generated in hybrid mode, then checked (refusal, citations, correctness).
"""
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import RateLimitError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from docassistant.answer import NOT_FOUND, answer  # noqa: E402
from docassistant.clients import openai_client  # noqa: E402
from docassistant.config import settings  # noqa: E402
from docassistant.evaluation import (  # noqa: E402
    as_sources, first_rank, hit, is_refusal, judge_messages, parse_citations, parse_verdict, recall, summarize,
)
from docassistant.search import MODES, retrieve  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
TOP = 5


def option(name: str, default: str) -> str:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


RUNS = int(option("--runs", "1"))
QUESTIONS_FILE = ROOT / option("--questions", "eval/questions.json")
RESULTS_FILE = ROOT / option("--out", "eval/results.json")


def with_retry(fn, attempts: int = 5):
    for attempt in range(attempts):
        try:
            return fn()
        except RateLimitError:
            wait = 2 ** attempt
            print(f"  rate limit, retry in {wait} s")
            time.sleep(wait)
    raise RuntimeError("Rate limit: giving up")


def judge(question: str, expected: str, text: str) -> bool:
    response = with_retry(
        lambda: openai_client().chat.completions.create(
            model=settings.chat_deployment, messages=judge_messages(question, expected, text)
        )
    )
    return parse_verdict(response.choices[0].message.content)


questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
runs: list[list[dict]] = [[] for _ in range(RUNS)]
details = []

for q in questions:
    print(f"[{q['id']}/{len(questions)}] {q['question']}")
    expected = as_sources(q["expected_sources"])
    answerable = q["expected_behavior"] == "answer"

    retrieved, texts, per_run = {}, [], []
    for run in range(RUNS):
        result = with_retry(lambda: answer(q["question"], top=TOP, mode="hybrid"))
        passages = [(p.source, p.page) for p in result.passages]
        if run == 0:  # retrieval metrics come from the first run (the approximate vector search can vary slightly)
            retrieved["hybrid"] = passages
            for mode in ("keyword", "vector"):
                retrieved[mode] = [(p.source, p.page) for p in with_retry(lambda: retrieve(q["question"], top=TOP, mode=mode))]
        refused = is_refusal(result.text, NOT_FOUND)
        cited = parse_citations(result.text)
        correct = bool(answerable and not refused and judge(q["question"], q["expected_answer"], result.text))
        per_run.append({
            "refused": refused,
            "correct": correct,
            "cited_expected": bool(cited & set(expected)),
            "citations_valid": cited <= set(passages),
        })
        texts.append(result.text)

    retrieval = {
        "hit": {m: hit(expected, retrieved[m]) for m in MODES},
        "recall": {m: recall(expected, retrieved[m]) for m in MODES},
        "rank": {m: first_rank(expected, retrieved[m]) for m in MODES},
    }
    for run in range(RUNS):
        runs[run].append({"id": q["id"], "category": q["category"], "behavior": q["expected_behavior"],
                          **retrieval, **per_run[run]})
    details.append({
        "id": q["id"], "category": q["category"], "question": q["question"],
        "expected_behavior": q["expected_behavior"], "expected_answer": q["expected_answer"],
        "expected_sources": q["expected_sources"], "answers": texts, "per_run": per_run,
        "retrieved": {m: [list(s) for s in retrieved[m]] for m in MODES},
        "rank": retrieval["rank"],
    })

summaries = [summarize(r, MODES) for r in runs]
output = {
    "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "chat_deployment": settings.chat_deployment,
    "embedding_deployment": settings.embedding_deployment,
    "top": TOP,
    "runs": RUNS,
    "summaries": summaries,
    "questions": details,
}
RESULTS_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

s0 = summaries[0]
na, nr = s0["n_answerable"], s0["n_refusals"]


def across_runs(key: str) -> str:
    values = [s[key] for s in summaries]
    if RUNS == 1:
        return f"{values[0]}"
    return f"{sum(values) / RUNS:.1f} on average (runs: {', '.join(map(str, values))})"


print("\n" + "=" * 78)
print(f"RETRIEVAL: expected page in the top {TOP} ({na} answerable questions)")
print(f"  {'mode':8s} {'hit@5':>7s} {'hit@1':>7s} {'MRR':>7s} {'recall':>7s}")
for m in MODES:
    print(f"  {m:8s} {s0['retrieval_hit'][m]:>4d}/{na:<2d} {s0['retrieval_hit_at_1'][m]:>4d}/{na:<2d} "
          f"{s0['retrieval_mrr'][m]:>7.3f} {s0['retrieval_recall'][m]:>7.2f}")
print("  hit@5 by category:  " + "  ".join(f"{m:>8s}" for m in MODES))
for cat, row in s0["retrieval_hit_by_category"].items():
    print(f"    {cat:11s} (n={row['n']})   " + "  ".join(f"{str(row[m]) + '/' + str(row['n']):>8s}" for m in MODES))
print(f"\nGENERATION (hybrid, {RUNS} run{'s' if RUNS > 1 else ''})")
print(f"  correct answers        {across_runs('correct')} / {na}")
print(f"  cited an expected page {across_runs('cited_expected')} / {na}")
print(f"  false refusals         {across_runs('false_refusals')} / {na}")
print(f"  correct refusals       {across_runs('correct_refusals')} / {nr}")
print(f"  invalid citations      {across_runs('invalid_citations')} answer(s) citing a page that was not retrieved")

fail_counts = {}
for run in runs:
    for r in run:
        bad = ((r["behavior"] == "answer" and not r["correct"])
               or (r["behavior"] == "refuse" and not r["refused"]) or not r["citations_valid"])
        fail_counts[r["id"]] = fail_counts.get(r["id"], 0) + (1 if bad else 0)
to_review = {i: n for i, n in fail_counts.items() if n}
good = [i for i in fail_counts if i not in to_review]
random.seed(0)
print("\nTO REVIEW by hand (question id: number of failing runs): " + (str(to_review) if to_review else "none"))
print(f"Spot-check (random, never failed): {sorted(random.sample(good, min(5, len(good))))}")
print(f"Details: {RESULTS_FILE.relative_to(ROOT)}")
