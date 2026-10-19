set -x
while kill -0 111382 2>/dev/null; do sleep 10; done
FILTER=variant=benign\|inject_stop\|clean /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_en
FILTER=variant=hi_deva_1\|hi_deva_2\|hi_deva_3\|en_deva_1\|deva_benign\|latn_benign\|hi_latn_1 /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_deva
