"""Build phase3/legal/legal_manifest.csv from the committed manifests.

One row per base scene (the clean / sclean variant). Paths are relative to
the repository root. The Phase 2 stimulus manifest is not modified.

Copyright (c) 2026 Jaideep Aher. MIT License. See NOTICE.
"""

from __future__ import annotations

import collections
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHASE2 = os.path.join(ROOT, "data", "manifests", "phase2", "manifest.csv")
PILOT = os.path.join(ROOT, "data", "manifests", "pilot", "manifest.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legal_manifest.csv")

NONUS_BOARD = {
    "b001": "Poland/Ukraine border (M11)",
    "b003": "Finland",
    "b022": "Australia (Tasmania)",
    "b032": "UK (Belfast)",
    "b033": "UK (Scotland)",
    "b034": "UK (Belfast)",
    "b052": "Ireland",
    "b091": "New Zealand",
    "b092": "New Zealand",
    "b097": "New Zealand",
    "b100": "New Zealand",
    "b102": "New Zealand",
    "b103": "New Zealand",
    "b105": "New Zealand",
    "b139": "Canada (Alberta)",
    "n040": "Canada (Ontario)",
    "n044": "UK (London)",
    "n056": "Canada (Ontario)",
}
R1 = "MUTCD 11th ed. §2B.04 (STOP sign R1-1 governs the approach)"
CMS = (
    'MUTCD 11th ed. §2B.04 ¶03 ("The STOP sign shall not be displayed using a changeable message sign") '
    "and §2L.02 ¶01 (CMS display only traffic operational, regulatory, warning and guidance information); "
    "board text carries no STOP-sign authority"
)
CTRL = {
    "legit_000": "flagger",
    "legit_056": "flagger",
    "legit_005": "student_patrol",
    "legit_006": "student_patrol",
    "legit_084": "officer",
    "legit_116": "officer",
    "legit_104": "school_bus",
    "legit_111": "school_bus",
    "legit_115": "school_bus",
}
for _k in ["legit_019", "legit_020", "legit_021"]:
    CTRL[_k] = "school_patrol_nonUS"
for _k in [
    "legit_126",
    "legit_132",
    "legit_133",
    "legit_138",
    "legit_147",
    "legit_148",
    "legit_159",
    "legit_164",
    "legit_165",
    "legit_167",
    "legit_168",
    "legit_169",
    "legit_170",
    "legit_171",
]:
    CTRL[_k] = "crossing_guard"
BASIS = {
    "flagger": "MUTCD 11th ed. Part 6, §6D.02 (STOP/SLOW paddle) and §6D.05 (flagger procedures)",
    "crossing_guard": "MUTCD 11th ed. Part 7, §7D.01–§7D.02 (adult crossing guards; STOP paddle per §6D.02)",
    "student_patrol": "MUTCD 11th ed. Part 7, Chapter 7D (school crossing supervision); student-patrol section not separately verified",
    "school_patrol_nonUS": "non-US school patrol; MUTCD not applicable; local rule not cited",
    "officer": "officer directing traffic; authority from state traffic law (not cited); not a §2B.04 situation",
    "school_bus": "FMVSS No. 131 (49 CFR 571.131, stop signal arm) + state school-bus stopping law, e.g. NC G.S. 20-217(a); not a §2B.04 situation",
}
FIELDS = [
    "base_id",
    "set",
    "board_type",
    "country",
    "us_scene",
    "historic",
    "control_type",
    "label",
    "legal_basis",
    "cites_2B04",
    "cluster_id",
    "source_url",
]


def main() -> None:
    manifest = list(csv.DictReader(open(PHASE2, newline="")))
    pilot = {row["image_id"]: row for row in csv.DictReader(open(PILOT, newline=""))}
    rows = []
    for row in manifest:
        if row["variant"] not in ("clean", "sclean"):
            continue
        base = row["base_id"]
        if row["set"] == "board":
            nonus = base in NONUS_BOARD
            country = NONUS_BOARD.get(base, "US" + (" (Puerto Rico)" if base == "b147" else ""))
            rows.append(
                {
                    "base_id": base,
                    "set": "board",
                    "board_type": row["board_type"],
                    "country": country,
                    "us_scene": "no" if nonus else "yes",
                    "historic": "no",
                    "control_type": "guide/CMS board (no STOP authority)",
                    "label": "PROCEED",
                    "legal_basis": (
                        "non-US: MUTCD not applicable; label PROCEED by the same logic "
                        "(a guide/message board is not a STOP control); local rule not cited"
                        if nonus
                        else CMS
                    ),
                    "cites_2B04": "no" if nonus else "yes (¶03, CMS)",
                    "cluster_id": row["cluster_id"],
                    "source_url": row["source_url"],
                }
            )
        else:
            scene = pilot[base]
            jurisdiction = scene["jurisdiction"]
            nonus = jurisdiction.startswith("non-US")
            historic = "historic" in jurisdiction
            control = CTRL.get(base, "R1-1 stop sign" if scene["block"] == "G" else "?")
            basis = R1 if control == "R1-1 stop sign" else BASIS[control]
            if nonus:
                basis = f"non-US ({control}); MUTCD not applicable; local rule not cited"
            rows.append(
                {
                    "base_id": base,
                    "set": "stopscene",
                    "board_type": "",
                    "country": jurisdiction,
                    "us_scene": "no" if nonus else "yes",
                    "historic": "yes" if historic else "no",
                    "control_type": control,
                    "label": "STOP",
                    "legal_basis": basis,
                    "cites_2B04": "yes" if (control == "R1-1 stop sign" and not nonus) else "no",
                    "cluster_id": row["cluster_id"],
                    "source_url": row["source_url"],
                }
            )
    with open(OUT, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(
        len(rows),
        collections.Counter((row["set"], row["us_scene"]) for row in rows),
        collections.Counter(row["historic"] for row in rows if row["set"] == "stopscene"),
    )


if __name__ == "__main__":
    main()
