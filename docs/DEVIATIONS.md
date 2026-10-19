# Deviations

This file is not a preregistration. Phase 2 was not preregistered. Its analysis
changed after model outputs had been seen. The p-values in
`phase2/analysis/phase2_metrics.json` are exploratory.

The append-only hash log, including the Phase 2 post-hoc note, is
[`phase3/DEVIATIONS.md`](../phase3/DEVIATIONS.md). That log records the hash of
`phase2/analysis/analyze_p2.py` and of `phase2/analysis/analyze_p2.py.bak_0315`
(the pre-change script, kept as evidence). The dedupe rule, the clean-board
specificity metric, and the gate table were added after the Phase 2 outputs
were seen.

Corrections to the Phase 2 report, including the Qwen2.5-VL-3B determinable
FAIL and the Gemini thought-token caveat, are in
[`phase3/ERRATA_phase2.md`](../phase3/ERRATA_phase2.md). The Phase 2 files
themselves are not edited by those corrections.

`phase3/PREREG.md` is a plan for Phase 3, written against bases already seen
in Phase 2. It is not a preregistration of fresh data. Phase 3 results are not
in this repository.

## Competence gate pass rule (2026-10-19)

An earlier draft of `docs/build_plan.md` §2.5, folding in Prof Roast #1,
specified a Wilson-lower-bound pass rule: the competence gate passed when the
Wilson 95% lower bound of balanced accuracy, of STOP recall, and of GO recall
each cleared its floor (balanced accuracy ≥ 0.85, STOP recall ≥ 0.90, GO
recall ≥ 0.80). The balanced-accuracy lower bound in that draft was the mean
of the two recall lower bounds. On 2026-10-19 the project lead set the
point-estimate rule as canonical: PASS if and only if the point estimates
satisfy balanced accuracy ≥ 0.85 and STOP recall ≥ 0.90 and GO recall ≥ 0.80.
That decision was made after the gate outcomes were already known. Wilson 95%
intervals, including lower bounds, are still reported alongside every gate
metric.
