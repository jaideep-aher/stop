set -x
FILTER=arm=en\|proceed_at_stop /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv p1 main
FILTER=variant=benign\|inject_stop /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_en
FILTER=variant=hi_deva_1\|en_deva_1\|deva_benign\|latn_benign\|hi_latn_1 /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_deva
FILTER=block=G /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/pilot/v2work/pilot_v2/manifest.csv n2,n3 gate
