set -x
while kill -0 111382 2>/dev/null; do sleep 10; done
FILTER=variant=benign\|inject_stop /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_en
FILTER=variant=hi_deva_1\|en_deva_1\|deva_benign\|latn_benign\|hi_latn_1 /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_deva
/workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/real_manifest.csv n2 real
FILTER=arm=deva /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/manifest.csv n2 deva
N=$(cat /workspace/rai_pivot/phase2/run/results_gemini_*.jsonl | wc -l); if [ $((N+110)) -le 1600 ]; then /workspace/rai_pivot/pilot/venv/bin/python run_p2.py gemini /workspace/rai_pivot/phase2/stimuli/manifest_wording2.csv n3 wording2; else echo "skip wording2 N=$N"; fi
