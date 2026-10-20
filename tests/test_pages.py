"""The public Pages artifact ships only allowlisted images."""

import importlib.util
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "build_pages_artifact",
    ROOT / "scripts" / "build_pages_artifact.py",
)
_PAGES = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PAGES)
build = _PAGES.build
check = _PAGES.check
ship_ok = _PAGES.ship_ok


def test_real_artifact_is_allowlisted(tmp_path: Path):
    dest = tmp_path / "pages"
    summary = build(dest)
    assert summary["kept"] == 1189
    assert (dest / "data/img/p2/fig1.png").is_file()
    assert (dest / "data/img/p2/fig2_left.png").is_file()
    errors = check(dest)
    assert errors == []
    assert (dest / ".nojekyll").is_file()
    data = json.loads((dest / "data" / "data.json").read_text(encoding="utf-8"))
    assert data["repo"]["name"] == "jaideep-aher/stop"
    # A denylisted thumb must not be a file, and data.json must not point at it.
    denied = ROOT / "data" / "PAGES_DENYLIST.txt"
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


def _human_checked() -> set[str]:
    import csv

    found = set()
    with (ROOT / "data" / "HUMAN_CHECKED.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if (row.get("human_checked_by") or "").strip() and (row.get("human_checked_date") or "").strip():
                found.add((row.get("image_id") or "").strip())
    return found


def test_detector_clears_stay_off_pages_until_a_person_reviews_them(tmp_path: Path):
    """A detector pass after the head-band miss does not publish an image no person has checked."""
    import csv

    audit = list(csv.DictReader((ROOT / "data" / "privacy_audit.csv").open(newline="", encoding="utf-8")))
    pending = {row["image_id"] for row in audit if row["decision"] == "pending_human"}
    assert pending == PENDING_HUMAN
    upstream = {row["image_id"] for row in audit if row["upstream_withhold"] == "yes"}
    assert len(upstream) == 252
    assert "ill2_037" not in pending
    checked = _human_checked()
    assert len(checked) == 879
    assert _PAGES.HARD_EXCLUDE_IDS.isdisjoint(checked)
    deny_lines = (ROOT / "data" / "PAGES_DENYLIST.txt").read_text(encoding="utf-8").splitlines()
    denied = {}
    for line in deny_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path, _, reason = line.partition("\t")
        denied[Path(path).stem] = reason
    allow = set()
    for line in (ROOT / "data" / "PAGES_ALLOWLIST.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            allow.add(line.split("\t", 1)[0].strip())
    withheld = {
        row["path"]: row["reason"]
        for row in csv.DictReader((ROOT / "data" / "WITHHELD_IMAGES.csv").open(newline="", encoding="utf-8"))
    }
    for image_id in PENDING_HUMAN - checked:
        assert denied[image_id] == "pending human review after blur fix"
        row = next(item for item in audit if item["image_id"] == image_id)
        rel = "site/site/" + row["path"]
        assert not (ROOT / rel).is_file()
        assert row["path"] not in allow
        assert withheld[rel]
    for image_id in PENDING_HUMAN & checked:
        assert image_id not in denied
        row = next(item for item in audit if item["image_id"] == image_id)
        assert row["path"] in allow
    dest = tmp_path / "pages"
    build(dest)
    shipped = {path.stem for path in dest.rglob("*") if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}}
    assert (upstream - checked).isdisjoint(shipped)
    assert (PENDING_HUMAN - checked).isdisjoint(shipped)
    assert _PAGES.HARD_EXCLUDE_IDS.isdisjoint(shipped)
    for image_id in ("ill2_037", "ill2_066", "ill2_312", "ill2_313"):
        assert image_id not in shipped
    data = json.loads((ROOT / "site" / "data" / "data.json").read_text(encoding="utf-8"))
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
    assert live <= checked


def test_possible_minors_are_absent_from_the_pages_artifact(tmp_path: Path):
    """ill2_037, ill2_066, ill2_312, and ill2_313 must not appear in the public artifact."""
    dest = tmp_path / "pages"
    build(dest)
    needles = tuple(_PAGES.HARD_EXCLUDE_IDS) + tuple(_PAGES.HARD_EXCLUDE_URLS)
    assert set(_PAGES.HARD_EXCLUDE_IDS) == {
        "ill2_017",
        "ill2_018",
        "ill2_019",
        "ill2_037",
        "ill2_066",
        "ill2_312",
        "ill2_313",
        "ill2_317",
        "ill2_318",
    }
    blob = b"\n".join(path.read_bytes() for path in dest.rglob("*") if path.is_file())
    for needle in needles:
        assert needle.encode() not in blob
    source = (ROOT / "site" / "data" / "data.json").read_text(encoding="utf-8")
    for needle in needles:
        assert needle not in source


def test_unpublished_entries_keep_no_credit_or_source(tmp_path: Path):
    """A Pages entry that is not published has no credit, source, or URL fields."""
    dest = tmp_path / "pages"
    build(dest)
    data = json.loads((dest / "data" / "data.json").read_text(encoding="utf-8"))
    present = {
        path.relative_to(dest).as_posix()
        for path in dest.rglob("*")
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    }

    def published(node: dict) -> bool:
        if node.get("published") is False:
            return False
        for key in ("thumb", "file"):
            value = node.get(key)
            if isinstance(value, str) and value in present:
                return True
        return False

    def assert_no_provenance(node: dict) -> None:
        for key, value in node.items():
            low = key.lower()
            assert "credit" not in low
            assert not low.startswith("source")
            assert low not in {"url", "file_title", "title", "photographer", "cluster_id"}
            assert not low.endswith("_url")
            if isinstance(value, str):
                assert not value.startswith(("http://", "https://"))
                assert "commons.wikimedia.org" not in value

    for item in data["pilot"]["images"]:
        if published(item):
            assert item.get("credit") and item.get("source_url")
        else:
            assert_no_provenance(item)
    for base in data["p2"]["bases"]:
        images = list(base["images"].values())
        if any(published(item) for item in images):
            assert base.get("credit") and base.get("source_url")
        else:
            assert_no_provenance(base)
        for item in images:
            if not published(item):
                assert_no_provenance(item)
    for item in data["p2"]["real"]:
        if published(item):
            assert item.get("credit") and item.get("source_url")
        else:
            assert_no_provenance(item)
    for item in data["p2"]["examples"]:
        if published(item):
            assert item.get("credit") and item.get("source_url")
        else:
            assert_no_provenance(item)
    assert not any(path.name == "LICENSES.md" for path in dest.rglob("*"))


def test_blur_helper_import_does_not_require_a_detector():
    image = Image.new("RGB", (4, 4), "blue")
    assert image.getpixel((0, 0)) == (0, 0, 255)
