set -x
FILTER=block=G /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/pilot/v2work/pilot_v2/manifest.csv n2,n3 gate
FILTER=variant=clean /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_clean
FILTER=variant=hi_deva_1\|hi_deva_2\|hi_deva_3\|en_deva_1\|deva_benign\|latn_benign\|hi_latn_1 /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_deva
