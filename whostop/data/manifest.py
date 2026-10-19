"""Load a stimulus manifest and check the fields the publish filter needs.

Column names differ between the pilot manifest and the Phase 2 manifests.
``sha256_16`` fills ``sha256``. ``blur_status`` fills ``blur``. Missing
``needs_human_check`` stays missing: the publish filter treats that as not
cleared.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from pathlib import Path

_SHA_KEYS = ("sha256", "sha256_16")
_BLUR_KEYS = ("blur", "blur_status")


def load_manifest(path: Path | str) -> list[dict]:
    """Read a CSV manifest into normalized row dicts."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [normalize_row(row) for row in csv.DictReader(handle)]


def normalize_row(row: Mapping) -> dict:
    """Copy ``row`` and fill canonical license, credit, source, hash, and blur fields."""
    out = dict(row)
    _fill(out, "sha256", _SHA_KEYS)
    _fill(out, "blur", _BLUR_KEYS)
    edited = str(out.get("edited") or "").strip().lower()
    out["edited_flag"] = edited in {"yes", "true", "1", "y"} or edited.startswith("yes")
    flag = str(out.get("needs_human_check") or "").strip().lower()
    if flag in {"yes", "true", "1", "y"}:
        out["needs_human_check_flag"] = True
    elif flag in {"no", "false", "0", "n"}:
        out["needs_human_check_flag"] = False
    else:
        out["needs_human_check_flag"] = None
    return out


def _fill(row: dict, canonical: str, keys: Sequence[str]) -> None:
    if str(row.get(canonical) or "").strip():
        return
    for key in keys:
        value = row.get(key)
        if str(value or "").strip():
            row[canonical] = value
            return


def validate_manifest(rows: Sequence[Mapping]) -> list[dict]:
    """Return one issue dict per row that is missing a required field.

    Required: license, credit, source_url, sha256, blur, an explicit
    needs_human_check (yes or no), and an edited flag (the column may be
    ``no``). ``edited_flag`` is false when the column is absent, and that
    absence is reported.
    """
    issues = []
    for index, row in enumerate(rows):
        normalized = row if "edited_flag" in row else normalize_row(row)
        missing = []
        for field in ("license", "credit", "source_url", "sha256", "blur"):
            if not str(normalized.get(field) or "").strip():
                missing.append(field)
        if normalized.get("needs_human_check_flag") is None:
            missing.append("needs_human_check")
        if not str(normalized.get("edited") or "").strip():
            missing.append("edited")
        if missing:
            issues.append(
                {
                    "row": index,
                    "image_id": normalized.get("image_id"),
                    "missing": missing,
                }
            )
    return issues
