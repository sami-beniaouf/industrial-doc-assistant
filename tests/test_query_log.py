import json

from docassistant.query_log import log_event


def test_log_event_appends_valid_json_lines(tmp_path):
    path = tmp_path / "logs" / "queries.jsonl"
    log_event({"type": "query", "question": "Gants sur une rouleuse ?"}, path)
    log_event({"type": "feedback", "rating": "up"}, path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["type"] == "query" and "time" in first
    assert first["question"] == "Gants sur une rouleuse ?"
    assert json.loads(lines[1])["rating"] == "up"
