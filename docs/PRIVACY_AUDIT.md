# Privacy audit (2026-10-19)

## Root cause

The pilot display blur blurred only the top 22% of each YOLO person box, plus Haar faces at `minNeighbors=6`. This is not a coordinate-offset bug.

Checked on the committed `ill2_037` blurred file (`d1c2892ab36f4d205c39d1a9cb7f5de3f78be8f39e11facfad233442462d5335`, the same sha256 as the site developer's upstream file):

- Size is 960×640, the same frame the display copy uses.
- No EXIF orientation.
- The three person boxes in the developer's note (y 444–637, 446–638, 530–637) put the head strip at y 486.46, 488.24, and 553.54.
- YuNet on that file finds faces whose boxes run from about y 475 to y 624, below those strips.

Crowd and protest boxes are cut off by the frame. The top of the box is hair, a raised arm, or a placard, so the strip ends above the face.

## Fix

`person_blur_box` returns the whole xyxy rectangle. `yunet_blur_box` pads a YuNet face 30% on each side. The weights are opencv_zoo `face_detection_yunet_2023mar.onnx`, sha256 `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` (pinned in `models.lock` and `whostop/data/blur.py`). The `.onnx` file is git-ignored. `tests/test_blur.py` checks that a face below the old strip is inside the full person box, and that the YuNet pad is 30% per side.

`whostop/data/blur.py` returns the full person box and the padded YuNet face. A caller should refuse to run if the YuNet file's sha256 does not match the pin.

## Audit

`scripts/privacy_audit.py` ran Haar (frontal and profile, `minNeighbors=3`) and YuNet (score 0.45, plus a 2× pass) on every allowlisted Pages image. A hit was re-blurred over the full person region around the face (and any HOG person box that overlaps that face), including the 30% YuNet pad. An image on the developer's withhold list was cleared only when that re-blur left both detectors empty. Otherwise it stayed denied. Rows are in `data/privacy_audit.csv`. The withhold list is `data/upstream_withhold.csv` (252 ids).

## Reconciliation with the 252 withheld images

| decision | count |
|---|---|
| Detector-empty after re-blur, then held for a person (`pending_human`) | 52 |
| Kept denied (already not on the allow list) | 90 |
| Kept denied (no face detection to re-blur) | 86 |
| Kept denied (no region applied) | 21 |
| Kept denied (a detector still fired after the re-blur) | 3 |

The Pages allow list went from 483 paths to 373 when this audit denied the upstream withholds it did not clear. A detector pass is not enough to publish an image after the head-band miss. Those 52 ids were on the denylist with reason `pending human review after blur fix`. Each removed path is listed in `data/WITHHELD_IMAGES.csv`. `site/data/data.json` shows withheld images as withheld.

Twelve previously published images that were not on the upstream list had a face hit and were re-blurred the same way. Both detectors were empty afterward. They follow the same rule and are on the denylist with the same reason: `example_2`, `example_3`, `b032_benign`, `b032_clean`, `stop2_002_sboard_benign`, `stop2_002_sboard_proceed`, `stop2_011_sboard_benign`, `stop2_011_sboard_proceed`, `stop2_011_sclean`, `stop2_117_sboard_benign`, `stop2_117_sboard_proceed`, `stop2_097__control_removed`.

Ids both detectors called empty after the full person-region re-blur, now pending human review:

`b022_bare_stop`, `b022_bb_benign_cmd`, `b022_bb_inject_stop`, `b022_benign`, `b022_benign_cmd`, `b022_clean`, `b022_inject_stop`, `b022_nonsense`, `b022_official`, `b032_bare_stop`, `b032_benign_cmd`, `b032_inject_stop`, `b032_nonsense`, `b032_official`, `b118_bare_stop`, `b118_benign`, `b118_benign_cmd`, `b118_inject_stop`, `b118_nonsense`, `b118_official`, `b127_bb_benign_cmd`, `board_118__benign`, `board_118__inject_stop`, `board_118__official`, `ill2_018`, `ill2_019`, `ill2_021`, `ill2_035`, `ill2_233`, `ill2_279`, `ill2_316`, `ill2_317`, `ill2_318`, `ill3_128`, `ill3_137`, `ill3_148`, `ill3_150`, `legit_005_sclean`, `legit_083`, `legit_133`, `legit_134`, `legit_138`, `legit_147`, `legit_148`, `legit_159`, `legit_165`, `legit_165_sboard_benign`, `legit_165_sboard_proceed`, `legit_165_sclean`, `stop2_025`, `stop2_030__sign_removed`, `stop2_178__control_removed`.

`ill2_037`, `ill2_066`, `ill2_312`, and `ill2_313` stay denied. Their committed image files were deleted.

Nothing on the public site relies on the two-detector check alone. Every id in `docs/upstream_withhold.csv` stays off the Pages artifact until a person has looked at the re-blurred file.

## Human check, 2026-10-19

Jaideep Aher checked 588 blurred copies (`data/HUMAN_CHECKED.csv`). Those paths are on `data/PAGES_ALLOWLIST.txt` and the files are in `data/images/`. `data/WITHHELD_IMAGES.csv` lists the 180 that remain off the site: 9 possible minors, held until each id is confirmed, and 171 blur re-check failures. The counts above describe the audit before that check.
