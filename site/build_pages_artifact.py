#!/usr/bin/env python3
"""Build the public GitHub Pages tree from ``site/site``.

The repository stays private. Pages is public, so an image is copied only when
all of the following hold:

- its path is listed in ``site/PAGES_ALLOWLIST.txt``
- its path is not listed in ``site/PAGES_DENYLIST.txt``
- no blur sidecar and not ``needs_human_check.csv`` flags that image id
- the record does not name Mapillary or BDD100K

``site/blurred/``, pilot and phase2 image directories, and raw-image directories
are not part of this web root and are not copied. ``data.json`` thumbs that
point at a dropped file are cleared so the page shows "withheld" instead of a
missing image. A ``.nojekyll`` file is written. Asset paths stay relative.

Usage:
    python site/build_pages_artifact.py --out _pages
    python site/build_pages_artifact.py --out _pages --check
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif"}
BLOCKED_SOURCE = re.compile(r"mapillary|bdd100k|bdd-100k|bdd_100k", re.IGNORECASE)
IMG_TAG = re.compile(r"<img\b[^>]*?\ssrc=\"([^\"]+)\"[^>]*>", re.IGNORECASE)
SKIP_DIRS = {"blurred", "raw", "private", "images_raw", "thumbs_real", "thumbs_board", "sheets"}

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "site" / "site"
ALLOW_PATH = REPO / "site" / "PAGES_ALLOWLIST.txt"
DENY_PATH = REPO / "site" / "PAGES_DENYLIST.txt"
# ids a person cleared after checking the blurred copy (human_checked_by, human_checked_date)
HUMAN_CHECKED_PATH = REPO / "site" / "HUMAN_CHECKED.csv"

# possible minors; excluded entirely
HARD_EXCLUDE_IDS = frozenset(
    {
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
)
HARD_EXCLUDE_URLS = frozenset(
    {
        "https://commons.wikimedia.org/wiki/File:"
        "Person_holding_a_protest_sign_with_text_%22Stop_Putin%22_(51949180000).jpg",
        "https://commons.wikimedia.org/wiki/File:"
        "Person_protesting_vaccine_mandate_in_Austria_is_holding_a_%22Stop_Discrimination%22_"
        "sign_(51694528225).jpg",
        "https://commons.wikimedia.org/wiki/File:"
        "Protester_holding_a_sign_that_reads_%22Stop_CO2_Emission%22_at_a_Global_Climate_Strike_"
        "(51059102311).jpg",
        "https://commons.wikimedia.org/wiki/File:"
        "Young_Black_Lives_Matter_activists_are_holding_a_colorful_Stop_Racism_sign_"
        "(50115127871).jpg",
        "https://commons.wikimedia.org/wiki/File:"
        "Person_at_Pride_parade_holding_sign_with_text_%22Stop_biphobia%22_(51262325481).jpg",
        "https://commons.wikimedia.org/wiki/File:"
        "Stop_Adani%27s_coal_mine_-_-climatestrike_Melbourne_IMG_3471_(45203191905).jpg",
        "https://commons.wikimedia.org/wiki/File:"
        "Stop_Climate_Change_Now_-_-climatestrike_Melbourne_IMG_3491_(45390723384).jpg",
        "https://commons.wikimedia.org/wiki/File:"
        "Stop_thinking_about_your_next_election,_start_thinking_about_OUR_future_-_-"
        "climatestrike_Melbourne_IMG_3477_(45203233755).jpg",
        "https://commons.wikimedia.org/wiki/File:"
        "Stop_thinking_about_your_next_election_-_-climatestrike_Melbourne_IMG_3519_"
        "(45390922084).jpg",
    }
)
# Identifying fields removed from any Pages entry that is not published.
_PROVENANCE_KEYS = frozenset(
    {
        "credit",
        "source_url",
        "source",
        "source_file",
        "url",
        "file_title",
        "title",
        "photographer",
        "cluster_id",
    }
)


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def load_path_list(path: Path) -> set[str]:
    found = set()
    if not path.is_file():
        return found
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rel = _norm(line.split("\t", 1)[0].strip())
        if rel:
            found.add(rel)
    return found


def flagged_ids(web: Path) -> set[str]:
    """Image ids whose sidecar says the blur still needs a person."""
    flagged = set()
    data = web / "data"
    if not data.is_dir():
        return flagged
    for csv_path in sorted(data.glob("*.csv")):
        with csv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                image_id = (row.get("image_id") or "").strip()
                if not image_id:
                    continue
                flag = (row.get("needs_human_check") or "").strip().lower()
                status = (row.get("blur_status") or "").strip().lower()
                reason = (row.get("reason") or row.get("check_reason") or "")
                if flag in {"yes", "true", "1"} or status.startswith("no_detections"):
                    flagged.add(image_id)
                elif csv_path.name == "needs_human_check.csv" and image_id:
                    flagged.add(image_id)
                elif "MANUAL REVIEW" in reason.upper():
                    flagged.add(image_id)
    return flagged - human_checked_ids()


def human_checked_ids() -> set[str]:
    """Ids with a recorded human check of the blurred copy; these flags are cleared."""
    if not HUMAN_CHECKED_PATH.is_file():
        return set()
    with HUMAN_CHECKED_PATH.open(newline="", encoding="utf-8") as handle:
        return {
            (row.get("image_id") or "").strip()
            for row in csv.DictReader(handle)
            if (row.get("human_checked_by") or "").strip() and (row.get("human_checked_date") or "").strip()
        }


def blocked_source_paths(payload: object, found: set[str]) -> None:
    """Collect thumb and file paths on any object that names a blocked source."""
    if isinstance(payload, dict):
        blob = " ".join(str(value) for value in payload.values() if isinstance(value, str))
        if BLOCKED_SOURCE.search(blob):
            for key in ("thumb", "file"):
                value = payload.get(key)
                if isinstance(value, str):
                    found.add(_norm(value))
            images = payload.get("images")
            if isinstance(images, dict):
                for image in images.values():
                    if isinstance(image, dict) and isinstance(image.get("thumb"), str):
                        found.add(_norm(image["thumb"]))
        for value in payload.values():
            blocked_source_paths(value, found)
    elif isinstance(payload, list):
        for value in payload:
            blocked_source_paths(value, found)


def manifest_blocked_paths() -> set[str]:
    """Refuse Mapillary / BDD100K rows even when they are not in data.json."""
    blocked = set()
    manifests = [
        REPO / "pilot" / "pilot_v2" / "manifest.csv",
        REPO / "phase2" / "stimuli" / "manifest.csv",
        REPO / "phase2" / "stimuli" / "real_manifest.csv",
    ]
    for path in manifests:
        if not path.is_file():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                blob = " ".join(str(value) for value in row.values())
                if not BLOCKED_SOURCE.search(blob):
                    continue
                image_id = row.get("image_id") or ""
                for rel in (
                    f"data/img/pilot/{image_id}.jpg",
                    f"data/img/p2/stim/{image_id}.jpg",
                    f"data/img/p2/real/{image_id}.jpg",
                ):
                    blocked.add(rel)
    return blocked


def ship_ok(rel: str, *, allow: set[str], deny: set[str], flagged: set[str], blocked: set[str]) -> bool:
    rel = _norm(rel)
    if Path(rel).stem in HARD_EXCLUDE_IDS:
        return False
    if rel in deny or rel in blocked or rel not in allow:
        return False
    if Path(rel).stem in flagged:
        return False
    if set(rel.split("/")) & SKIP_DIRS:
        return False
    return True


def _is_hard_excluded(node: object) -> bool:
    """True when a record names an id or Commons URL that must not be published."""
    if not isinstance(node, dict):
        return False
    ident = node.get("id")
    if isinstance(ident, str) and ident in HARD_EXCLUDE_IDS:
        return True
    url = node.get("source_url")
    if isinstance(url, str) and url in HARD_EXCLUDE_URLS:
        return True
    for key in ("thumb", "file"):
        value = node.get(key)
        if isinstance(value, str) and Path(value).stem in HARD_EXCLUDE_IDS:
            return True
    return False


def _drop_hard_excluded(node: object) -> None:
    """Remove excluded records so the artifact has no id, credit, caption, or URL."""
    if isinstance(node, dict):
        for key in list(node.keys()):
            value = node[key]
            if _is_hard_excluded(value):
                del node[key]
            else:
                _drop_hard_excluded(value)
    elif isinstance(node, list):
        node[:] = [item for item in node if not _is_hard_excluded(item)]
        for item in node:
            _drop_hard_excluded(item)


def _hard_exclude_needles() -> tuple[str, ...]:
    return tuple(HARD_EXCLUDE_IDS) + tuple(HARD_EXCLUDE_URLS)


def _is_provenance_key(key: str) -> bool:
    low = key.lower()
    return low in _PROVENANCE_KEYS or low.endswith("_url") or "credit" in low or low.startswith("source")


def _clear_provenance(node: dict) -> bool:
    """Drop credit, source URL, file title, and photographer id. Return whether any were set."""
    had = bool(node.get("credit") or node.get("source_url"))
    for key in list(node):
        if _is_provenance_key(key):
            node.pop(key, None)
    return had


def _image_is_published(node: dict, present: set[str]) -> bool:
    """A shipped image file, and not an explicit withhold."""
    if node.get("published") is False:
        return False
    for key in ("thumb", "file"):
        value = node.get(key)
        if isinstance(value, str) and _norm(value) in present:
            return True
    return False


def _scrub_copied_text(dest: Path) -> None:
    """Drop excluded ids and Commons URLs from every text file the artifact copied."""
    needles = _hard_exclude_needles()
    text_ext = {".json", ".csv", ".html", ".js", ".md", ".txt", ".css"}
    for path in list(dest.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in IMAGE_EXT and path.stem in HARD_EXCLUDE_IDS:
            path.unlink()
            continue
        if path.suffix.lower() not in text_ext:
            continue
        text = path.read_text(encoding="utf-8")
        if not any(needle in text for needle in needles):
            continue
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
            _drop_hard_excluded(payload)
            path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
            continue
        if path.suffix.lower() == ".csv":
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                fields = reader.fieldnames
                rows = [
                    row
                    for row in reader
                    if not any(needle in " ".join(row.values()) for needle in needles)
                ]
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields or [], lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            continue
        kept = [
            line
            for line in text.splitlines(keepends=True)
            if not any(needle in line for needle in needles)
        ]
        path.write_text("".join(kept), encoding="utf-8")


def _assert_hard_exclude_absent(dest: Path) -> None:
    needles = [item.encode() for item in _hard_exclude_needles()]
    for path in dest.rglob("*"):
        if not path.is_file():
            continue
        blob = path.read_bytes()
        for needle in needles:
            if needle in blob:
                rel = path.relative_to(dest).as_posix()
                raise SystemExit(f"hard-exclude still in artifact: {rel}")


def _scrub(node: object, present: set[str]) -> None:
    if isinstance(node, dict):
        for key in ("thumb", "file"):
            value = node.get(key)
            if isinstance(value, str) and Path(value).suffix.lower() in IMAGE_EXT:
                if _norm(value) not in present:
                    node[key] = None
                    if "published" in node:
                        node["published"] = False
                    refusal = node.get("refusal")
                    if isinstance(refusal, list) and "pages_withheld" not in refusal:
                        refusal.append("pages_withheld")
        for value in node.values():
            _scrub(value, present)
    elif isinstance(node, list):
        for value in node:
            _scrub(value, present)


def _strip_unpublished_provenance(data: dict, present: set[str]) -> int:
    """Unpublished entries keep an id only. Published images keep credit and license."""
    stripped = 0
    pilot = data.get("pilot")
    if isinstance(pilot, dict):
        for item in pilot.get("images") or []:
            if isinstance(item, dict) and not _image_is_published(item, present):
                if _clear_provenance(item):
                    stripped += 1
                item["published"] = False
                item["thumb"] = None
    phase2 = data.get("p2")
    if isinstance(phase2, dict):
        for base in phase2.get("bases") or []:
            images = list((base.get("images") or {}).values())
            if not any(isinstance(item, dict) and _image_is_published(item, present) for item in images):
                if _clear_provenance(base):
                    stripped += 1
            for item in images:
                if isinstance(item, dict) and not _image_is_published(item, present) and _clear_provenance(item):
                    stripped += 1
        for item in phase2.get("real") or []:
            if isinstance(item, dict) and not _image_is_published(item, present) and _clear_provenance(item):
                stripped += 1
        for item in phase2.get("examples") or []:
            if isinstance(item, dict) and not _image_is_published(item, present) and _clear_provenance(item):
                stripped += 1
    return stripped


def _scrub_public_tables(dest: Path, present: set[str]) -> None:
    """Public CSV rows for unpublished images keep the id and lose source paths."""
    published_ids = {Path(path).stem for path in present}
    for path in dest.rglob("*.csv"):
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        if not fields or "image_id" not in fields:
            continue
        kept = []
        changed = False
        for row in rows:
            image_id = (row.get("image_id") or "").strip()
            if image_id in HARD_EXCLUDE_IDS:
                changed = True
                continue
            if image_id not in published_ids:
                for key in list(row):
                    if _is_provenance_key(key) and row.get(key):
                        row[key] = ""
                        changed = True
            kept.append(row)
        if not changed:
            continue
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(kept)


def _rewrite_data(dest: Path, present: set[str]) -> int:
    path = dest / "data" / "data.json"
    if not path.is_file():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    dropped = 0

    def _count_dropped(node: object) -> None:
        nonlocal dropped
        if isinstance(node, dict):
            if _is_hard_excluded(node) and (node.get("credit") or node.get("source_url")):
                dropped += 1
            for value in node.values():
                _count_dropped(value)
        elif isinstance(node, list):
            for value in node:
                _count_dropped(value)

    _count_dropped(data)
    _drop_hard_excluded(data)
    _scrub(data, present)
    stripped = _strip_unpublished_provenance(data, present)
    phase2 = data.get("p2")
    if isinstance(phase2, dict):
        examples = phase2.get("examples")
        if isinstance(examples, list):
            phase2["examples"] = [item for item in examples if item.get("file")]
        bases = phase2.get("bases") or []
        published = 0
        stimuli = 0
        for base in bases:
            for image in (base.get("images") or {}).values():
                stimuli += 1
                if image.get("thumb"):
                    published += 1
        phase2["n_published"] = published
        if stimuli:
            phase2["n_stimuli"] = stimuli
        figs = phase2.get("figs")
        if isinstance(figs, dict):
            for key, value in list(figs.items()):
                if isinstance(value, str) and _norm(value) not in present:
                    figs[key] = None
        real = phase2.get("real")
        if isinstance(real, list):
            for item in real:
                if not item.get("thumb"):
                    item["thumb"] = None
    pilot = data.get("pilot")
    if isinstance(pilot, dict) and isinstance(pilot.get("images"), list):
        for item in pilot["images"]:
            if not item.get("thumb"):
                item["published"] = False
                item["thumb"] = None
        pilot["n_published"] = sum(1 for item in pilot["images"] if item.get("published") and item.get("thumb"))
        refusals = pilot.get("refusals")
        if isinstance(refusals, dict):
            refusals["visible_face"] = sum(
                1 for item in pilot["images"] if "visible_face" in (item.get("refusal") or [])
            )
    if isinstance(data.get("repo"), dict):
        data["repo"]["name"] = "jaideep-aher/stop"
        data["repo"]["status"] = "private repository; this Pages build is the filtered public site"
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    return stripped + dropped


def _rewrite_html(dest: Path, present: set[str]) -> None:
    path = dest / "index.html"
    if not path.is_file():
        return
    html = path.read_text(encoding="utf-8")

    def replace(match: re.Match) -> str:
        src = match.group(1)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        rel = _norm(src.split("?", 1)[0].split("#", 1)[0])
        if Path(rel).suffix.lower() not in IMAGE_EXT:
            return match.group(0)
        if rel in present and (dest / rel).is_file():
            return match.group(0)
        return '<span class="noimg">image withheld</span>'

    path.write_text(IMG_TAG.sub(replace, html), encoding="utf-8")


def build(dest: Path) -> dict:
    if not WEB.is_dir():
        raise SystemExit(f"missing web root: {WEB}")
    allow = load_path_list(ALLOW_PATH)
    deny = load_path_list(DENY_PATH)
    flagged = flagged_ids(WEB)
    raw = json.loads((WEB / "data" / "data.json").read_text(encoding="utf-8"))
    blocked: set[str] = set()
    blocked_source_paths(raw, blocked)
    blocked |= manifest_blocked_paths()
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(WEB, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    kept = 0
    dropped = 0
    for path in list(dest.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXT:
            continue
        rel = path.relative_to(dest).as_posix()
        if ship_ok(rel, allow=allow, deny=deny, flagged=flagged, blocked=blocked):
            kept += 1
        else:
            path.unlink()
            dropped += 1
    present = {
        path.relative_to(dest).as_posix()
        for path in dest.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXT
    }
    stripped = _rewrite_data(dest, present)
    _rewrite_html(dest, present)
    _scrub_public_tables(dest, present)
    _scrub_copied_text(dest)
    _assert_hard_exclude_absent(dest)
    (dest / ".nojekyll").write_text("", encoding="utf-8")
    return {
        "kept": kept,
        "dropped": dropped,
        "allow": len(allow),
        "flagged_ids": len(flagged),
        "provenance_stripped": stripped,
    }


def check(dest: Path) -> list[str]:
    """Fail when a shipped image is outside the allowlist or a JSON thumb is missing."""
    allow = load_path_list(ALLOW_PATH)
    deny = load_path_list(DENY_PATH)
    flagged = flagged_ids(WEB)
    errors = []
    for path in dest.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXT:
            continue
        rel = path.relative_to(dest).as_posix()
        if rel not in allow:
            errors.append(f"non-allowlisted image: {rel}")
        if rel in deny:
            errors.append(f"denylisted image: {rel}")
        if Path(rel).stem in flagged:
            errors.append(f"flagged image: {rel}")
        if set(rel.split("/")) & SKIP_DIRS:
            errors.append(f"excluded directory image: {rel}")
    data_path = dest / "data" / "data.json"
    if data_path.is_file():
        payload = json.loads(data_path.read_text(encoding="utf-8"))

        def walk(node: object) -> None:
            if isinstance(node, dict):
                blob = " ".join(str(value) for value in node.values() if isinstance(value, str))
                for key in ("thumb", "file"):
                    value = node.get(key)
                    if not isinstance(value, str) or Path(value).suffix.lower() not in IMAGE_EXT:
                        continue
                    rel = _norm(value)
                    if not (dest / rel).is_file():
                        errors.append(f"data.json points at a missing file: {rel}")
                    if BLOCKED_SOURCE.search(blob):
                        errors.append(f"data.json still shows a blocked source image: {rel}")
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(payload)
    index = dest / "index.html"
    if index.is_file():
        for match in IMG_TAG.finditer(index.read_text(encoding="utf-8")):
            src = match.group(1)
            if src.startswith(("http://", "https://", "data:")):
                continue
            rel = _norm(src.split("?", 1)[0])
            if Path(rel).suffix.lower() in IMAGE_EXT and not (dest / rel).is_file():
                errors.append(f"index.html points at a missing image: {rel}")
    if not (dest / ".nojekyll").is_file():
        errors.append("missing .nojekyll")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the filtered GitHub Pages artifact.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Exit 1 if the artifact breaks the filter.")
    args = parser.parse_args(argv)
    summary = build(args.out)
    print(
        f"pages artifact {args.out}: kept {summary['kept']} images, "
        f"dropped {summary['dropped']}, allowlist {summary['allow']}, "
        f"flagged ids {summary['flagged_ids']}, "
        f"withheld entries stripped of credit {summary['provenance_stripped']}"
    )
    if args.check:
        errors = check(args.out)
        if errors:
            print("\n".join(errors[:50]))
            print(f"{len(errors)} filter error(s)")
            return 1
        print("pages filter check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
