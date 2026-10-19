"""Every tracked image is allowlisted, a no-photo chart, or a reviewed poster composite."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOW = ROOT / "site" / "PAGES_ALLOWLIST.txt"
CHARTS = ROOT / "site" / "NONPHOTO_IMAGES.txt"
COMPOSITES = ROOT / "poster" / "REVIEWED_COMPOSITES.txt"
WITHHELD = ROOT / "docs" / "WITHHELD_IMAGES.csv"


def _first_field(path: Path) -> set[str]:
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        found.add(line.split("\t", 1)[0].split(",", 1)[0].strip())
    return found


def _tracked() -> list[str]:
    output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return [line for line in output.splitlines() if line]


def test_tracked_images_are_allowlisted_or_charts():
    allow = _first_field(ALLOW)
    charts = _first_field(CHARTS)
    composites = _first_field(COMPOSITES)
    assert composites
    assert composites.isdisjoint(charts)
    assert all(not rel.startswith("site/site/") for rel in composites)
    bad = []
    for rel in _tracked():
        if Path(rel).suffix.lower() not in IMAGE_EXT:
            continue
        if rel.startswith("site/site/") and rel[len("site/site/") :] in allow:
            continue
        if rel in charts:
            continue
        if rel in composites:
            continue
        bad.append(rel)
    assert bad == []


def test_withheld_list_matches_removed_images_and_is_not_tracked():
    listed = _first_field(WITHHELD)
    assert listed
    tracked = set(_tracked())
    still_tracked = sorted(listed & tracked)
    assert still_tracked == []
    missing_rows = [rel for rel in listed if (ROOT / rel).is_file()]
    assert missing_rows == []
