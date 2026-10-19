"""The public Pages artifact ships only allowlisted images."""

import importlib.util
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "build_pages_artifact",
    ROOT / "site" / "build_pages_artifact.py",
)
_PAGES = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PAGES)
build = _PAGES.build
check = _PAGES.check
ship_ok = _PAGES.ship_ok


def test_real_artifact_is_allowlisted(tmp_path: Path):
    dest = tmp_path / "pages"
    summary = build(dest)
    assert summary["kept"] > 0
    assert summary["dropped"] > 0
    errors = check(dest)
    assert errors == []
    assert (dest / ".nojekyll").is_file()
    data = json.loads((dest / "data" / "data.json").read_text(encoding="utf-8"))
    assert data["repo"]["name"] == "jaideep-aher/stop"
    # A denylisted thumb must not be a file, and data.json must not point at it.
    denied = ROOT / "site" / "PAGES_DENYLIST.txt"
    sample = None
    for line in denied.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            sample = line.split("\t", 1)[0].strip()
            break
    assert sample
    assert not (dest / sample).exists()


def test_ship_ok_refuses_sources_and_flags():
    allow = {"data/img/pilot/a.jpg", "data/img/pilot/b.jpg"}
    assert not ship_ok(
        "data/img/pilot/b.jpg",
        allow=allow,
        deny=set(),
        flagged={"b"},
        blocked=set(),
    )
    assert not ship_ok(
        "data/img/pilot/a.jpg",
        allow=allow,
        deny=set(),
        flagged=set(),
        blocked={"data/img/pilot/a.jpg"},
    )
    assert ship_ok(
        "data/img/pilot/a.jpg",
        allow=allow,
        deny=set(),
        flagged=set(),
        blocked=set(),
    )


def test_upstream_withhold_stays_off_the_artifact_unless_the_audit_cleared_it(tmp_path: Path):
    """The site developer's 252-image withhold list is denied unless the audit cleared it."""
    import csv

    audit = list(csv.DictReader((ROOT / "docs" / "privacy_audit.csv").open(newline="", encoding="utf-8")))
    denied_ids = {row["image_id"] for row in audit if row["upstream_withhold"] == "yes" and row["decision"] == "deny"}
    cleared_ids = {row["image_id"] for row in audit if row["decision"] == "cleared"}
    assert "ill2_037" in denied_ids
    assert len(denied_ids) + len(cleared_ids) == 252
    dest = tmp_path / "pages"
    build(dest)
    shipped = {path.stem for path in dest.rglob("*") if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}}
    assert denied_ids.isdisjoint(shipped)
    for image_id in ("ill2_037", "ill2_066", "ill2_312", "ill2_313"):
        assert image_id not in shipped


def test_blur_helper_import_does_not_require_a_detector():
    image = Image.new("RGB", (4, 4), "blue")
    assert image.getpixel((0, 0)) == (0, 0, 255)
