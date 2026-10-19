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


PENDING_HUMAN = {
    "b022_bare_stop",
    "b022_bb_benign_cmd",
    "b022_bb_inject_stop",
    "b022_benign",
    "b022_benign_cmd",
    "b022_clean",
    "b022_inject_stop",
    "b022_nonsense",
    "b022_official",
    "b032_bare_stop",
    "b032_benign",
    "b032_benign_cmd",
    "b032_clean",
    "b032_inject_stop",
    "b032_nonsense",
    "b032_official",
    "b118_bare_stop",
    "b118_benign",
    "b118_benign_cmd",
    "b118_inject_stop",
    "b118_nonsense",
    "b118_official",
    "b127_bb_benign_cmd",
    "board_118__benign",
    "board_118__inject_stop",
    "board_118__official",
    "example_2",
    "example_3",
    "ill2_018",
    "ill2_019",
    "ill2_021",
    "ill2_035",
    "ill2_233",
    "ill2_279",
    "ill2_316",
    "ill2_317",
    "ill2_318",
    "ill3_128",
    "ill3_137",
    "ill3_148",
    "ill3_150",
    "legit_005_sclean",
    "legit_083",
    "legit_133",
    "legit_134",
    "legit_138",
    "legit_147",
    "legit_148",
    "legit_159",
    "legit_165",
    "legit_165_sboard_benign",
    "legit_165_sboard_proceed",
    "legit_165_sclean",
    "stop2_002_sboard_benign",
    "stop2_002_sboard_proceed",
    "stop2_011_sboard_benign",
    "stop2_011_sboard_proceed",
    "stop2_011_sclean",
    "stop2_025",
    "stop2_030__sign_removed",
    "stop2_097__control_removed",
    "stop2_117_sboard_benign",
    "stop2_117_sboard_proceed",
    "stop2_178__control_removed",
}


def test_detector_clears_stay_off_pages_until_a_person_reviews_them(tmp_path: Path):
    """A detector pass after the head-band miss does not publish an image."""
    import csv

    audit = list(csv.DictReader((ROOT / "docs" / "privacy_audit.csv").open(newline="", encoding="utf-8")))
    pending = {row["image_id"] for row in audit if row["decision"] == "pending_human"}
    assert pending == PENDING_HUMAN
    upstream = {row["image_id"] for row in audit if row["upstream_withhold"] == "yes"}
    assert len(upstream) == 252
    assert "ill2_037" not in pending
    deny_lines = (ROOT / "site" / "PAGES_DENYLIST.txt").read_text(encoding="utf-8").splitlines()
    denied = {}
    for line in deny_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path, _, reason = line.partition("\t")
        denied[Path(path).stem] = reason
    for image_id in PENDING_HUMAN:
        assert denied[image_id] == "pending human review after blur fix"
        row = next(item for item in audit if item["image_id"] == image_id)
        assert (ROOT / "site" / "site" / row["path"]).is_file()
    dest = tmp_path / "pages"
    build(dest)
    shipped = {path.stem for path in dest.rglob("*") if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}}
    assert upstream.isdisjoint(shipped)
    assert PENDING_HUMAN.isdisjoint(shipped)
    for image_id in ("ill2_037", "ill2_066", "ill2_312", "ill2_313"):
        assert image_id not in shipped
    data = json.loads((ROOT / "site" / "site" / "data" / "data.json").read_text(encoding="utf-8"))
    live = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            image_id = node.get("id")
            if image_id in PENDING_HUMAN and node.get("thumb"):
                live.add(image_id)
            file_name = node.get("file")
            if isinstance(file_name, str) and Path(file_name).stem in PENDING_HUMAN:
                live.add(Path(file_name).stem)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    assert live == set()


def test_possible_minors_are_absent_from_the_pages_artifact(tmp_path: Path):
    """ill2_037, ill2_066, ill2_312, and ill2_313 must not appear in the public artifact."""
    dest = tmp_path / "pages"
    build(dest)
    needles = tuple(_PAGES.HARD_EXCLUDE_IDS) + tuple(_PAGES.HARD_EXCLUDE_URLS)
    assert set(_PAGES.HARD_EXCLUDE_IDS) == {"ill2_037", "ill2_066", "ill2_312", "ill2_313"}
    blob = b"\n".join(path.read_bytes() for path in dest.rglob("*") if path.is_file())
    for needle in needles:
        assert needle.encode() not in blob
    source = (ROOT / "site" / "site" / "data" / "data.json").read_text(encoding="utf-8")
    for needle in needles:
        assert needle not in source


def test_blur_helper_import_does_not_require_a_detector():
    image = Image.new("RGB", (4, 4), "blue")
    assert image.getpixel((0, 0)) == (0, 0, 255)
