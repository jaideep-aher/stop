import json
from pathlib import Path

from whostop.score import score_record, tally


def test_score_record_skips_errors_and_parses(tmp_path: Path):
    path = tmp_path / "results.jsonl"
    rows = [
        {"image_id": "a", "raw": "STOP because the sign faces the car", "prompt": "p1"},
        {"image_id": "b", "raw": "ERROR timeout", "prompt": "p1"},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    from whostop.score import load_jsonl

    loaded = load_jsonl(path)
    assert score_record(loaded[0])["action"] == "STOP"
    assert score_record(loaded[1])["error"] is True
    counts = tally(loaded)
    assert counts["STOP"] == 1
    assert counts["ERROR"] == 1
    assert counts["n"] == 2
