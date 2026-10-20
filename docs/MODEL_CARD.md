# Model card

The runs used local GGUF weights through llama.cpp release b11723 (CPU, no GPU) and the Gemini API. `configs/models.lock` records the local sha256 of each GGUF the scripts loaded. This repository does not ship the weights.

| Model | Role |
|---|---|
| Qwen3-VL-2B | Pilot and Phase 2 headline model. One Phase 2 wording (p1) passes the competence gate on point estimates. |
| Gemini Flash (`gemini-3.8-flash`) | Frontier reference. Thinking was requested off; the API still reported thought tokens. |
| SmolVLM-500M | Pilot and Phase 2. Does not clear the gate. |
| SmolVLM2-2.2B | Phase 2 gate only. Does not clear the gate. |
| Qwen2.5-VL-3B | Phase 2 gate only. Determinable FAIL, not an incomplete run. |
| InternVL3-2B | Phase 3. Fails the gate on the word prompts. Passes both gates with letter answers. Not run on the study arms. |
| LFM2-VL-1.6B | Phase 3 second model. Passes on the word prompt at 448 px (n2). Fails the gate with letter answers. |
| YOLO | Detector used to build the Phase 2 gate set (block G). Phase 3 adds a gate that does not use YOLO. |

A parsed STOP or PROCEED is a decision-layer output on one still frame. It is not a claim that a vehicle would stop or go.
