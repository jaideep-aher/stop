set -x
FILTER=arm=en\|proceed_at_stop /workspace/rai_pivot/pilot/venv/bin/python run_p2.py smolvlm /workspace/rai_pivot/phase2/stimuli/manifest.csv p1 main
FILTER=variant=benign\|inject_stop /workspace/rai_pivot/pilot/venv/bin/python run_p2.py smolvlm /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_en
/workspace/rai_pivot/pilot/venv/bin/python run_p2.py smolvlm /workspace/rai_pivot/phase2/stimuli/real_manifest.csv p1 real
