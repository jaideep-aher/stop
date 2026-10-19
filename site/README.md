# Who Gets to Say STOP? Project site (local build)

Static site in `site/` (plain HTML/JS, no build step). All numbers come from metrics JSON files in this
repository (`phase2/`, `pilot/`). Rebuild scripts resolve the repo root relative to this folder.

## Rebuild (one command)
    ./rebuild.sh            # blur + build site/data/data.json   (same as: make data)
    ./rebuild.sh --serve    # ...then serve http://127.0.0.1:8765 (same as: make serve)
    ./rebuild.sh --fresh    # force the YOLO pass to re-run (otherwise it re-runs only when a set's input list changes)

Steps:
1. `make_blur_inputs.py` builds the image lists from the manifests.
2. `run_blur.sh` makes detector-based blurred copies in `blurred/` (YOLO11n plus Haar).
3. The same step writes the sidecars `site/data/*_blur.csv`, each with a `needs_human_check` and a `check_reason` column.
4. `site/build_site_data.py` writes `site/data/data.json`, the thumbnails and `site/data/needs_human_check.csv`.

Publication rules (enforced by the builder):
- An image needs a license, a credit and a blurred copy.
- Images with no detections are withheld as "pending human check".
- Pilot images waiting on plate review are withheld.
- An example pair is shown only if none of its images is flagged.
- If a spec pair is flagged, it is replaced deterministically: same conditions, model and verdict pattern, first unflagged base in id order. It is never chosen by effectiveness. Pair 6 (script arm) is never used.
- Captions show the verdict only.

## Clearing human checks
`site/data/needs_human_check.csv` lists every flagged image with its reason and site status. Reasons:
- edited legend hit by a face or plate box;
- face box outside any person;
- no detections (withheld).

After a person has checked the blurred copy, the safest way to clear a row is to add a manual allow-list. That is not built yet; for now the flags only block publication or example use.

## Adding a new phase (e.g. Phase 3 robustness)
1. Have the analysis write its metrics JSON, for example `phase3/analysis/phase3_metrics.json` at the repo root.
2. Make sure there is an entry in `site/phases.json` (Phase 3 is already listed):
       {"id": "phase3", "title": "Phase 3: robustness", "blurb": "...", "metrics": "phase3/analysis/phase3_metrics.json"}
   `metrics` is relative to the repository root (or absolute).
3. Run `./rebuild.sh`.

What the site shows:
- **While the file is missing:** a "Pending final run" empty state. Nothing is estimated.
- **Once it exists:** every result object shaped like `{k, n, rate, ci95}` is shown as k/n with its Wilson CI, labelled by its JSON path (model › condition › measure), in file order.
- **Never shown:** results are never sorted or ranked. Keys starting with `_` are skipped.

Per-phrase results must not be put in the JSON, or must sit under a `_`-prefixed key. The site aggregates by condition only.

New stimuli need extra work:
- Add the set to `make_blur_inputs.py` and to the loop in `run_blur.sh`.
- Add the matching publish step in `build_site_data.py`.
