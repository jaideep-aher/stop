"""Two-detector privacy audit of the Pages publish set.

Reads the site developer's withhold table, runs Haar and YuNet on every
allowlisted image, and re-blurs a hit with the full person region plus a
YuNet face padded 30% per side. An upstream withhold stays denied unless
that re-blur leaves both detectors empty. Writes data/privacy_audit.csv
and updates the allow list, deny list, and data.json. The 252-id withhold
table is data/upstream_withhold.csv.

Copyright (c) 2026 Jaideep Aher. MIT License. See NOTICE.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from whostop.data.blur import YUNET_SHA256, yunet_blur_box  # noqa: E402

YUNET = Path(os.environ.get("WHOSTOP_YUNET", "/tmp/models/face_detection_yunet_2023mar.onnx"))
ALLOW = ROOT / "data" / "PAGES_ALLOWLIST.txt"
DENY = ROOT / "data" / "PAGES_DENYLIST.txt"
DATA = ROOT / "site" / "data" / "data.json"
WEB = ROOT / "site"
WITHHOLD = ROOT / "data" / "upstream_withhold.csv"


def parse_withhold(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in path.read_text().splitlines():
        if not line.startswith("| ") or line.startswith("| image_id") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        image_id, set_, original, upstream, reason = cells[:5]
        if not image_id or image_id == "image_id":
            continue
        rows[image_id] = {
            "image_id": image_id,
            "set": set_,
            "sha256_original": original,
            "sha256_upstream_blurred": upstream,
            "reason": reason,
        }
    return rows


def load_list(path: Path) -> list[str]:
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line.split("\t")[0])
    return out


def yunet_boxes(det, img) -> list[tuple[float, float, float, float]]:
    found: list[tuple[float, float, float, float]] = []
    height, width = img.shape[:2]
    det.setInputSize((width, height))
    _, faces = det.detect(img)
    if faces is not None:
        for row in faces:
            found.append(tuple(float(v) for v in row[:4]))
    if width * 2 <= 4000 and height * 2 <= 4000:
        big = cv2.resize(img, (width * 2, height * 2), interpolation=cv2.INTER_LINEAR)
        det.setInputSize((width * 2, height * 2))
        _, faces = det.detect(big)
        if faces is not None:
            for row in faces:
                x, y, w, h = (float(v) for v in row[:4])
                found.append((x / 2, y / 2, w / 2, h / 2))
    return found


def haar_boxes(frontal, profile, gray) -> list[tuple[float, float, float, float]]:
    found = []
    for cascade in (frontal, profile):
        hits = cascade.detectMultiScale(gray, 1.1, 3, minSize=(12, 12))
        for x, y, w, h in hits:
            found.append((float(x), float(y), float(w), float(h)))
    return found


def hog_boxes(hog, img) -> list[tuple[float, float, float, float]]:
    rects, _ = hog.detectMultiScale(img, winStride=(8, 8), padding=(8, 8), scale=1.05)
    if rects is None or len(rects) == 0:
        return []
    return [(float(x), float(y), float(w), float(h)) for x, y, w, h in rects]


def xywh_to_xyxy(box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x, y, w, h = box
    return (x, y, x + w, y + h)


def overlaps(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def heavy(img, box) -> bool:
    height, width = img.shape[:2]
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return False
    roi = img[y0:y1, x0:x1]
    rh, rw = roi.shape[:2]
    small = cv2.resize(roi, (max(1, rw // 28), max(1, rh // 28)), interpolation=cv2.INTER_AREA)
    img[y0:y1, x0:x1] = cv2.resize(small, (rw, rh), interpolation=cv2.INTER_NEAREST)
    return True


def person_region(face_xywh: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """A full person rectangle around a face: hair above, torso below, wider than the face."""
    x, y, w, h = face_xywh
    return (x - 0.6 * w, y - 0.6 * h, x + 1.6 * w, y + 3.8 * h)


def regions_for(faces: list[tuple[float, float, float, float]], persons: list[tuple[float, float, float, float]]):
    boxes = []
    face_xyxy = [xywh_to_xyxy(face) for face in faces]
    for face in faces:
        boxes.append(yunet_blur_box(face, 0.3))
        boxes.append(person_region(face))
    for person in persons:
        person_xyxy = xywh_to_xyxy(person)
        if any(overlaps(person_xyxy, face) for face in face_xyxy):
            boxes.append(person_xyxy)
    return boxes


def recount(data: dict) -> None:
    p2 = data.get("p2", {})
    bases = p2.get("bases") or p2.get("boards") or {}
    if isinstance(bases, dict) and bases and "images" in next(iter(bases.values())):
        p2["n_published"] = sum(
            1 for base in bases.values() for image in base.get("images", {}).values() if image.get("thumb")
        )
    real = p2.get("real") or p2.get("real_tampered") or []
    if isinstance(real, list):
        p2["n_real_published"] = sum(1 for row in real if isinstance(row, dict) and row.get("thumb"))
    pilot = data.get("pilot", {})
    images = pilot.get("images") or []
    if isinstance(images, list):
        pilot["n_published"] = sum(1 for row in images if isinstance(row, dict) and row.get("published") and row.get("thumb"))


def walk_records(obj, fn) -> None:
    if isinstance(obj, dict):
        if "image_id" in obj and ("thumb" in obj or "published" in obj):
            fn(obj)
        for value in obj.values():
            walk_records(value, fn)
    elif isinstance(obj, list):
        for value in obj:
            walk_records(value, fn)


def main() -> None:
    digest = __import__("hashlib").sha256(YUNET.read_bytes()).hexdigest()
    if digest != YUNET_SHA256:
        raise SystemExit(f"YuNet sha256 {digest} != {YUNET_SHA256}")
    withhold = {
        row["image_id"]: row
        for row in csv.DictReader(WITHHOLD.open(newline="", encoding="utf-8"))
    }
    if len(withhold) != 252:
        raise SystemExit(f"expected 252 withheld ids, parsed {len(withhold)}")

    allow = load_list(ALLOW)
    allow_by_stem = {}
    for rel in allow:
        allow_by_stem.setdefault(Path(rel).stem, []).append(rel)

    det = cv2.FaceDetectorYN.create(str(YUNET), "", (320, 320), 0.45, 0.3, 5000)
    cascades = cv2.data.haarcascades
    frontal = cv2.CascadeClassifier(cascades + "haarcascade_frontalface_default.xml")
    profile = cv2.CascadeClassifier(cascades + "haarcascade_profileface.xml")
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    audit_rows = []
    deny_paths: dict[str, str] = {}
    cleared = []
    for index, rel in enumerate(allow, start=1):
        path = WEB / rel
        stem = Path(rel).stem
        on_list = stem in withhold
        if not path.is_file():
            audit_rows.append(
                {
                    "image_id": stem,
                    "path": rel,
                    "upstream_withhold": "yes" if on_list else "no",
                    "haar_before": "",
                    "yunet_before": "",
                    "hog_before": "",
                    "action": "missing_file",
                    "decision": "deny",
                    "note": "allowlisted path missing on disk",
                }
            )
            deny_paths[rel] = "allowlisted file missing"
            continue
        image = cv2.imread(str(path))
        if image is None:
            audit_rows.append(
                {
                    "image_id": stem,
                    "path": rel,
                    "upstream_withhold": "yes" if on_list else "no",
                    "haar_before": "",
                    "yunet_before": "",
                    "hog_before": "",
                    "action": "unreadable",
                    "decision": "deny",
                    "note": "cv2 could not read the file",
                }
            )
            deny_paths[rel] = "unreadable image"
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        haar = haar_boxes(frontal, profile, gray)
        yunet = yunet_boxes(det, image)
        persons = hog_boxes(hog, image) if (haar or yunet or on_list) else []
        faces = haar + yunet
        decision = "keep"
        action = "clean"
        note = ""
        if faces or (on_list and persons):
            boxes = regions_for(faces, persons)
            changed = image.copy()
            applied = sum(heavy(changed, box) for box in boxes)
            gray2 = cv2.cvtColor(changed, cv2.COLOR_BGR2GRAY)
            haar_after = haar_boxes(frontal, profile, gray2)
            yunet_after = yunet_boxes(det, changed)
            clean = not haar_after and not yunet_after and applied > 0
            if on_list:
                if clean:
                    decision = "cleared"
                    action = "full_person_reblur"
                    note = "upstream withhold cleared: both detectors empty after full person region + 30% YuNet pad"
                    cv2.imwrite(str(path), changed, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    cleared.append(stem)
                else:
                    decision = "deny"
                    action = "reblur_still_flagged" if applied else "no_region"
                    note = (
                        f"upstream withhold kept: haar_after={len(haar_after)} yunet_after={len(yunet_after)} "
                        f"regions={applied}"
                    )
                    deny_paths[rel] = "upstream withhold; full-person reblur did not clear both detectors"
            elif clean:
                decision = "keep"
                action = "full_person_reblur"
                note = "faces re-blurred; both detectors empty afterward"
                cv2.imwrite(str(path), changed, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            else:
                decision = "deny"
                action = "reblur_still_flagged"
                note = f"still flagged after full-person reblur: haar={len(haar_after)} yunet={len(yunet_after)}"
                deny_paths[rel] = "face still detected after full-person reblur"
        elif on_list:
            decision = "deny"
            action = "no_face_to_reblur"
            note = "upstream withhold kept: no face for a full-person reblur, so it is not cleared"
            deny_paths[rel] = "upstream withhold; two-detector audit did not clear it"
        audit_rows.append(
            {
                "image_id": stem,
                "path": rel,
                "upstream_withhold": "yes" if on_list else "no",
                "haar_before": len(haar),
                "yunet_before": len(yunet),
                "hog_before": len(persons),
                "action": action,
                "decision": decision,
                "note": note,
            }
        )
        if index % 50 == 0:
            print(f"audited {index}/{len(allow)}", flush=True)

    # Upstream ids that are not on the allow list stay denied. Record them.
    allow_stems = set(allow_by_stem)
    for image_id, row in sorted(withhold.items()):
        if image_id in allow_stems:
            continue
        audit_rows.append(
            {
                "image_id": image_id,
                "path": "",
                "upstream_withhold": "yes",
                "haar_before": "",
                "yunet_before": "",
                "hog_before": "",
                "action": "already_not_published",
                "decision": "deny",
                "note": f"not on the Pages allow list ({row['set']}); kept denied",
            }
        )

    denied_stems = {Path(path).stem for path in deny_paths}
    # Drop denied paths from the allow list and delete the web copies.
    new_allow = [rel for rel in allow if rel not in deny_paths]
    header = ALLOW.read_text().splitlines()[0]
    ALLOW.write_text(header + "\n" + "\n".join(new_allow) + "\n")
    deny_lines = [line for line in DENY.read_text().splitlines() if line.strip()]
    existing = {line.split("\t")[0] for line in deny_lines if not line.startswith("#")}
    for rel, reason in sorted(deny_paths.items()):
        if rel not in existing:
            deny_lines.append(f"{rel}\t{reason}")
        web = WEB / rel
        if web.is_file():
            web.unlink()
        blurred = ROOT / "data" / "images" / Path(rel).name
        if blurred.is_file():
            blurred.unlink()
    DENY.write_text("\n".join(deny_lines) + "\n")

    data = json.loads(DATA.read_text())

    def scrub(record: dict) -> None:
        if record.get("image_id") not in denied_stems:
            return
        record["published"] = False
        record["thumb"] = None
        refusal = record.get("refusal") or []
        if isinstance(refusal, str):
            refusal = [refusal] if refusal else []
        if "visible_face" not in refusal:
            refusal.append("visible_face")
        record["refusal"] = refusal

    walk_records(data, scrub)
    recount(data)
    DATA.write_text(json.dumps(data, separators=(",", ":")))

    csv_path = ROOT / "data" / "privacy_audit.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "image_id",
                "path",
                "upstream_withhold",
                "haar_before",
                "yunet_before",
                "hog_before",
                "action",
                "decision",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(audit_rows)

    n_clear = sum(1 for row in audit_rows if row["decision"] == "cleared")
    n_deny_new = len(deny_paths)
    n_keep = sum(1 for row in audit_rows if row["decision"] == "keep")
    print(f"allow {len(allow)} -> {len(new_allow)}; newly denied {n_deny_new}; cleared {n_clear}; kept {n_keep}")
    print("cleared ids:", ", ".join(sorted(set(cleared))) or "(none)")


if __name__ == "__main__":
    main()
