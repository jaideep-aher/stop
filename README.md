# Who Gets to Say STOP?

I tested whether a small vision model treats words on a roadside board as a command to stop or go, even when that board has no legal authority to control the car.

Live site: https://who-gets-to-say-stop-site-production.up.railway.app

My poster: [poster/poster.pdf](poster/poster.pdf)

## Why it matters

Waymo recalled 3,067 robotaxis after the software "reasoned that it should proceed" past a stopped school bus ([recall 25E-084](https://static.nhtsa.gov/odi/rcl/2025/RCLRPT-25E084-7732.pdf)). NHTSA is probing about 2.88 million Teslas ([PE25012](https://static.nhtsa.gov/odi/inv/2025/INOA-PE25012-19171.pdf)), and a Tesla has braked for a STOP on a billboard ([incident record](https://www.aiaaic.org/aiaaic-repository/ai-algorithmic-and-automation-incidents/tesla-autopilot-confused-by-billboard)). Cars are adding small vision-language models ([Waymo's Driving VLM](https://waymo.com/blog/2025/12/demonstrably-safe-ai-for-autonomous-driving), [DriveVLM](https://arxiv.org/abs/2402.12289)). I tested models that can run on a CPU.

## Question

Does a vision-language model, on one driver-view frame, treat roadside text as a stop or go instruction when that text has no legal authority?

Authority, in one line: under the MUTCD, a stop may be ordered by a flagger, a crossing guard, a school-bus stop arm, or police. A billboard, a carried sign, or a digitally edited board cannot.

A changeable message sign shall not display a STOP sign ([§2B.04](https://mutcd.fhwa.dot.gov/pdfs/11th_Edition/part2b.pdf)).

## What I did

I used real licensed photos, blurred faces and plates, and edited only the board text: 63 highway boards and 71 real stop scenes. A count required a competence gate on point estimates: at least 90% STOP on real stop signs, 80% GO on open roads, and balanced accuracy at least 0.85. LFM2-VL-1.6B and InternVL3-2B pass that gate. Gemini Flash passed on more than one wording. Three other small models failed, and I do not use their rates.

## What I found

Qwen3-VL-2B, main wording; this wording misses the stricter gate.

| Contrast | Count |
|---|---|
| Injected stop text vs a benign board | 62/63 vs 13/63 |
| PROCEED board at a real stop | 45/71 vs 14/71 |

Letter answers on that wording fell to 16/71 and 22/71, against 0/71. That shrink is consistent with copying. This test does not show that copying is the cause. A board in the lane was 30/32 against 10/32.

The setting that passes every gate gives 63/63 vs 17/63 and 48/71 vs 2/71. I chose that setting after seeing the results.

LFM2-VL-1.6B passes the gate: 43/71 vs 14/71 on a PROCEED board. Gemini Flash was 0/71 on that board.

### Robustness checks

InternVL3-2B passes the gate. The injected stop was 62/63 vs 9/63, and 62/63 vs 10/63 on the other letter mapping.

## Recommendation

Safety cases for SOTIF (ISO 21448) and UL 4600, and reviews by NHTSA or a state, should test whether a STOP is obeyed only from a legitimate MUTCD source.

## Limitations and future work

- Labels come from a single labeler; a second human rater and agreement statistics are future work.
- These are edited still photos. A parsed STOP or PROCEED is not a claim that a car would stop or go.

Next I want more in-car models, and video with more than one frame.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make reproduce
pytest
```

`make reproduce` rebuilds the metrics and fails if they differ.

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

The code is MIT. See [LICENSE](LICENSE). Photographs keep their own credit and license in [docs/LICENSES.md](docs/LICENSES.md). What I withheld is in [docs/PRIVACY_AUDIT.md](docs/PRIVACY_AUDIT.md).

Cursor was used to help in this project.
