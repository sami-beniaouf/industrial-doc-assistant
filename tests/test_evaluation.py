from docassistant.evaluation import (
    as_sources,
    first_rank,
    hit,
    is_refusal,
    parse_citations,
    parse_verdict,
    recall,
    summarize,
)

NOT_FOUND = "Je ne trouve pas cette information dans les documents."


def test_parse_citations_handles_several_formats():
    text = "Règle A [suva_travail_des_metaux.pdf, p. 24]. Règle B [a.pdf, p.3; b.pdf, p. 10]."
    assert parse_citations(text) == {("suva_travail_des_metaux.pdf", 24), ("a.pdf", 3), ("b.pdf", 10)}


def test_parse_citations_none():
    assert parse_citations("Aucune source ici.") == set()


def test_is_refusal_ignores_quotes_and_period():
    assert is_refusal(NOT_FOUND, NOT_FOUND)
    assert is_refusal("« Je ne trouve pas cette information dans les documents. »", NOT_FOUND)
    assert not is_refusal("Je ne trouve pas, mais l'aluminium fond à 660 °C.", NOT_FOUND)


def test_hit_and_recall():
    expected = as_sources([["a.pdf", 1], ["b.pdf", 2]])
    retrieved = [("b.pdf", 2), ("c.pdf", 9)]
    assert hit(expected, retrieved)
    assert recall(expected, retrieved) == 0.5
    assert not hit(expected, [("c.pdf", 9)])


def test_parse_verdict():
    assert parse_verdict("OUI")
    assert parse_verdict(" oui.")
    assert not parse_verdict("NON")


def test_summarize_counts():
    modes = ("hybrid", "keyword")
    results = [
        {"category": "fact", "behavior": "answer", "hit": {"hybrid": True, "keyword": False},
         "recall": {"hybrid": 1.0, "keyword": 0.0}, "rank": {"hybrid": 1, "keyword": None}, "refused": False, "correct": True,
         "cited_expected": True, "citations_valid": True},
        {"category": "fact", "behavior": "answer", "hit": {"hybrid": False, "keyword": False},
         "recall": {"hybrid": 0.0, "keyword": 0.0}, "rank": {"hybrid": 4, "keyword": None}, "refused": True, "correct": False,
         "cited_expected": False, "citations_valid": True},
        {"category": "out_of_scope", "behavior": "refuse", "hit": {"hybrid": False, "keyword": False},
         "recall": {"hybrid": 1.0, "keyword": 1.0}, "rank": {"hybrid": None, "keyword": None}, "refused": True, "correct": False,
         "cited_expected": False, "citations_valid": True},
    ]
    s = summarize(results, modes)
    assert s["n_answerable"] == 2 and s["n_refusals"] == 1
    assert s["retrieval_hit"] == {"hybrid": 1, "keyword": 0}
    assert s["correct"] == 1 and s["false_refusals"] == 1 and s["correct_refusals"] == 1
    assert s["retrieval_hit_by_category"]["fact"]["hybrid"] == 1
    assert s["retrieval_hit_at_1"] == {"hybrid": 1, "keyword": 0}
    assert abs(s["retrieval_mrr"]["hybrid"] - (1 + 0.25) / 2) < 1e-9


def test_first_rank():
    expected = as_sources([["a.pdf", 1], ["b.pdf", 2]])
    assert first_rank(expected, [("c.pdf", 9), ("b.pdf", 2), ("a.pdf", 1)]) == 2
    assert first_rank(expected, [("c.pdf", 9)]) is None
