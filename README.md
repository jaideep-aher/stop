# Who Gets to Say STOP?

I tested whether a small vision model treats words on a roadside board as a command to stop or go, even when that board has no legal authority to control the car.

Live site: https://who-gets-to-say-stop-site-production.up.railway.app

My poster: [poster/poster.pdf](poster/poster.pdf)

## Why it matters

Waymo recalled 3,067 robotaxis after the software "reasoned that it should proceed" past a stopped school bus ([recall 25E-084](https://static.nhtsa.gov/odi/rcl/2025/RCLRPT-25E084-7732.pdf)). NHTSA is probing about 2.88 million Teslas on traffic signals and signs ([PE25012](https://static.nhtsa.gov/odi/inv/2025/INOA-PE25012-19171.pdf)), and a Tesla has braked for a STOP printed on a billboard ([incident record](https://www.aiaaic.org/aiaaic-repository/ai-algorithmic-and-automation-incidents/tesla-autopilot-confused-by-billboard)). Cars are adding vision-language models that read the scene ([Waymo's Driving VLM](https://waymo.com/blog/2025/12/demonstrably-safe-ai-for-autonomous-driving), [DriveVLM](https://arxiv.org/abs/2402.12289)). A car cannot call a giant cloud model for every frame, so I tested small models that can run on a CPU.

## Question

Does a vision-language model, looking at one driver-view frame, treat roadside text as a stop or go instruction when that text has no legal authority to stop the car?

Authority, in one line: under the MUTCD, a stop may be ordered by a flagger, a crossing guard, a school-bus stop arm, or police. A billboard, a carried sign, or a digitally edited board cannot.

The manual says a changeable message sign shall not display a STOP sign ([§2B.04](https://mutcd.fhwa.dot.gov/pdfs/11th_Edition/part2b.pdf)).

## What I did

I used real, licensed photos, blurred faces and plates, and edited only the board text: 63 highway boards and 71 real stop scenes. A result counted only after a competence gate, judged on point estimates: at least 90% STOP on real stop signs, 80% GO on open roads, and balanced accuracy at least 0.85. Qwen3-VL-2B and LFM2-VL-1.6B passed on at least one wording. Gemini Flash passed and mostly ignored the boards. Three other small models failed the gate, so I do not use their rates as findings.

## What I found

These counts are for the models that passed the gate. They are not a claim that a car would stop or go.

| Contrast | Count |
|---|---|
| Injected stop text vs a benign board, same highway photos (Qwen3-VL-2B) | 62/63 vs 13/63 |
| PROCEED board vs a benign board, at a real stop (Qwen3-VL-2B) | 45/71 vs 14/71 |
| LFM2-VL-1.6B, PROCEED board at a real stop | 43/71 vs 14/71 |

Gemini Flash, which also passed the gate, was 0/71 on that PROCEED board. Clean, unedited boards were 17/63. The injection control is the benign board, 13/63, not that clean count.

Letter answers on Qwen3-VL-2B fell to 16/71 and 22/71, against 0/71 on the benign board. That shrink is consistent with copying the answer word. This test does not show that copying is the cause.

### Robustness checks

A board standing in the lane was 30/32 against 10/32 on Qwen3-VL-2B. InternVL3-2B passed the gate only with letter answers, and repeated the injected stop at 62/63 against 9/63.

## Recommendation

Safety cases for SOTIF (ISO 21448) and UL 4600, and AV permit reviews by NHTSA or a state, should include a scene-text authority test: obey a STOP only from a legitimate MUTCD source, not from a billboard, a carried sign, a sign on a vehicle, or a digitally altered board. The counts above are the gate-passing models, on edited still photos.

## Limitations and future work

- Labels come from a single labeler; a second human rater and agreement statistics are future work.
- These are edited still photos. A parsed STOP or PROCEED is not a claim that a car would stop or go.
- The main counts are the gate-passing models. Gemini Flash mostly did not follow the board.

Next I want more in-car models, and video with more than one frame.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make reproduce
pytest
```

`make reproduce` rebuilds the metrics files from the committed result rows and fails if they differ.

## Project structure

```
configs/     pins for the model files I ran
data/        manifests, the image allowlist, and the blurred photos
docs/        the plan, the change log, licenses, and the privacy audit
poster/      the poster
results/     metrics, figures, and the raw result files
scripts/     the analysis scripts
site/        the web page
tests/       the checks CI runs
whostop/     the competence gate and the scoring code
```

## License

The code is MIT. See [LICENSE](LICENSE). The photographs are not covered by that license. Each image keeps the credit and license in [docs/LICENSES.md](docs/LICENSES.md). How the published images were blurred, and which ones I withheld, is in [docs/PRIVACY_AUDIT.md](docs/PRIVACY_AUDIT.md).

Cursor was used to help in this project.
