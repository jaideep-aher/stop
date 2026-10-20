# Data card

Photographs are Wikimedia Commons files under CC0, public domain, CC BY, or CC BY-SA. The MIT license on the code does not cover them. Credits and source URLs are on the manifest rows.

| Set | Where it lives | What it is |
|---|---|---|
| Pilot manifest | `data/manifests/pilot/manifest.csv` | Block G competence images, board edits, and sign-removal pairs. |
| Phase 2 manifests | `data/manifests/phase2/` | Board ladder, real STOP scenes, and the second wording list. |
| Phase 3 manifests | `data/manifests/phase3/` | G1 (YOLO-assisted block G), G2 (no YOLO), and the study arms. |
| Legal sources | `data/legal/` | MUTCD and statute excerpts used to define a legitimate stop. |
| Published images | `data/images/` | Blurred copies on `data/PAGES_ALLOWLIST.txt` (1187 photographs) plus Fig 1 and Fig 2. |
| Withheld | `data/WITHHELD_IMAGES.csv` | 9 files not in the tree: possible minors, held until each id is confirmed. |
| Human check | `data/HUMAN_CHECKED.csv` | 879 blurred copies checked by Jaideep Aher on 2026-10-19. |

Labels are provisional and come from one labeler. There is no human κ. Edits are digital composites, marked modified. Blurred copies are derivatives. Share-alike terms still apply to CC BY-SA derivatives.

G2 labels were made before those model runs. The file hash is in `docs/changes.md`.
