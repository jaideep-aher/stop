"""Publish filter: a flagged or unblurred image is refused."""

from pathlib import Path

from PIL import Image
from whostop.data.manifest import load_manifest, validate_manifest
from whostop.data.publish import blur_boxes, decide_publication, is_redistributable_license

ROOT = Path(__file__).resolve().parents[1]


def _ok(**overrides) -> dict:
    row = {
        "image_id": "ex",
        "license": "CC BY-SA 4.0",
        "credit": "Example Photographer",
        "source_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
        "sha256": "abc123",
        "blur": "blurred (detector-based, unverified)",
        "needs_human_check": "no",
        "edited": "yes (digital)",
    }
    row.update(overrides)
    return row


def test_licenses_that_may_ship():
    for text in (
        "CC0",
        "CC0 1.0",
        "Public domain",
        "PD",
        "CC BY 2.0",
        "CC BY 2.5",
        "CC BY 4.0",
        "CC BY-SA 2.0",
        "CC BY-SA 2.5",
        "CC BY-SA 3.0",
        "CC BY-SA 4.0",
    ):
        assert is_redistributable_license(text), text
    for text in ("CC BY-NC 4.0", "CC BY-ND 2.0", "CC BY-NC-SA 4.0", "", "MIT"):
        assert not is_redistributable_license(text), text


def test_manifest_licenses_are_redistributable():
    paths = [
        ROOT / "data" / "manifests" / "pilot" / "manifest.csv",
        ROOT / "data" / "manifests" / "phase2" / "manifest.csv",
        ROOT / "data" / "manifests" / "phase2" / "real_manifest.csv",
    ]
    for path in paths:
        rows = load_manifest(path)
        assert rows
        for row in rows:
            assert is_redistributable_license(row["license"]), (path.name, row["license"])
            assert row["sha256"]


def test_flagged_and_unblurred_are_refused():
    flagged = decide_publication(_ok(needs_human_check="yes"), n_boxes=2)
    assert flagged["publish"] is False
    assert "needs_human_check" in flagged["reasons"]

    manual = decide_publication(
        _ok(blur="blurred (yolo); plate blur best-effort, MANUAL REVIEW"),
        n_boxes=1,
    )
    assert manual["publish"] is False

    unblurred = decide_publication(_ok(blur=""), n_boxes=0)
    assert unblurred["publish"] is False
    assert "unblurred" in unblurred["reasons"]

    missing_flag = decide_publication(_ok(needs_human_check=""), n_boxes=2)
    assert missing_flag["publish"] is False

    clean = decide_publication(_ok(), n_boxes=1)
    assert clean["publish"] is True
    assert clean["edited"] is True


def test_mapillary_and_bdd_are_refused_even_with_a_free_license():
    mapillary = decide_publication(
        _ok(source_url="https://www.mapillary.com/app/im/abc"),
        n_boxes=3,
    )
    assert mapillary["publish"] is False
    assert "nonredistributable_source" in mapillary["reasons"]
    bdd = decide_publication(_ok(source_url="https://bdd100k.com/frame"), n_boxes=3)
    assert bdd["publish"] is False


def test_pilot_manual_review_rows_are_refused():
    refused = 0
    for row in load_manifest(ROOT / "data" / "manifests" / "pilot" / "manifest.csv"):
        if "MANUAL REVIEW" in row["blur"].upper():
            decision = decide_publication(row)
            assert decision["publish"] is False
            refused += 1
    assert refused > 0


def test_validator_requires_the_publish_fields():
    issues = validate_manifest([{"image_id": "x", "license": "CC0"}])
    assert issues and "credit" in issues[0]["missing"]
    assert validate_manifest([_ok()]) == []


def test_blur_changes_pixels_inside_the_box_only():
    image = Image.new("RGB", (40, 40), (0, 0, 255))
    for x in range(24):
        for y in range(24):
            image.putpixel((x, y), ((x * 17) % 256, (y * 13) % 256, 0))
    before = image.getpixel((2, 2))
    blurred = blur_boxes(image, [(0, 0, 24, 24)])
    assert blurred.getpixel((2, 2)) != before
    assert blurred.getpixel((38, 38)) == (0, 0, 255)
    untouched = blur_boxes(image, [])
    assert untouched.getpixel((2, 2)) == before
    assert decide_publication(_ok(), n_boxes=0)["publish"] is False
