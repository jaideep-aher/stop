# Phase 3 Addendum A — post-hoc, exploratory

Plan: `PREREG.md` Addendum A (sha256 d990f9cc…, logged in `DEVIATIONS.md` at 09:48:15 ET before any run). Numbers from `results/phase3/phase3_addendum_metrics.json` (`scripts/analyze_addendum.py`). All runs 448 px, greedy, letter prompts L1 (A=halt) and L2 (C=halt). 0 ERROR rows, 0 unparsed rows. Labels are one labeler, no human check yet.

## Gates (point gate, G1 AND G2)
- InternVL3-2B L1: PASS (G1 STOP 45/45, GO 48/49; G2 STOP 36/37, GO 51/59). L2: PASS (G1 45/45, 47/49; G2 36/37, 53/59). Existing rows, no rerun.
- LFM2-VL-1.6B L1: FAIL (G2 GO 34/59; G1 GO 44/49). L2: FAIL (G1 GO 34/49, G2 GO 5/59: says "halt" almost always). Letter-arm results for LFM2 are gate-failed/descriptive.

## Key subset (63 board bases, 71 real-STOP scenes); STOP rate variant vs benign board, exact McNemar, Holm
| model/prompt | ROAD CLOSED | inject STOP | bare STOP | clean | PROCEED side: non-STOP, proceed vs benign board |
|---|---|---|---|---|---|
| InternVL3 L1 | 49 vs 9 /63 | 62 vs 9 | 60 vs 9 | 10 vs 9 (ns) | 16 vs 2 /71 (p=0.0001; cluster p=0.009) |
| InternVL3 L2 | 57 vs 10 | 62 vs 10 | 60 vs 10 | 14 vs 10 (ns) | 1 vs 0 /71 (ns) |
| LFM2 L1 (gate-failed) | 43 vs 14 | 59 vs 14 | 61 vs 14 | 17 vs 14 (ns) | 2 vs 0 /71 (ns) |
| LFM2 L2 (gate-failed) | 63 vs 48 | 63 vs 48 | 63 vs 48 | 53 vs 48 (ns) | 0 vs 0 /71 |
All STOP-side contrasts Holm p < 0.001 (cluster sign-flip p ≤ 0.0002). InternVL3 P arm (L1): right 8 vs 0 /48 (p=0.008), lane 8 vs 1 /32 (p=0.016); L2: 0 vs 0, 1 vs 1.
Reading: the STOP-side effect survives letter answers in a second gate-passing model (InternVL3) in both mappings. The PROCEED-side effect appears only under L1
(where B = "keep driving normally") and vanishes under L2, so it is not robust to letter mapping — consistent with the copying/position explanation.

## Photographer-capped gate (no new runs)
Cap: no photographer > 20% of a label within a gate set (reduced to floor(0.25×others), random.Random(7)). G1 STOP: formulanone 10→8 (45→43). G2 STOP: Michael Rivera 23→3
(37→17). PROCEED sides unaffected. Caveat: after capping Rivera, Mjrmtg holds 5/17 = 29% of capped G2 STOP (cap applied once, not iterated).
Result: pass/fail is unchanged for every model × prompt × px cell (Qwen 15 cells, InternVL3 5, LFM2 5), and also under leave-the-largest-photographer-out.
Gate passers stay: Qwen n3/448; InternVL3 L1, L2; LFM2 n2. Capped G2 STOP recall: Qwen n3/448 17/17, InternVL3 L1/L2 16/17, LFM2 n2 16/17. Small n (17) → wide CIs.

## Deviations
- Post-hoc addendum after all results seen; exploratory. 448 px only, greedy only, single run.
- LFM2 L1/L2 gate reused 23 partial G1 rows from 04:49; rest run today. LFM2 letter arms were run despite gate fail (reported as descriptive, as the addendum allowed).
- InternVL3 P arm (right/lane benign vs proceed, L1/L2) added as allowed by the addendum; LFM2 P arm with letters not run.
