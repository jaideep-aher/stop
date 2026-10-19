"""The package carries one competence gate. Horn OK's floors are not in it."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_does_not_reuse_the_retired_floors():
    banned = ("0.75", "0.60")
    for path in (ROOT / "whostop").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{path} contains {token}"
