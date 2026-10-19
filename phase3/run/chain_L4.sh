#!/bin/bash
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=$ROOT/pilot/venv/bin/python; S=$ROOT/phase3/stimuli; cd $ROOT/phase3/run
while pgrep -f "run_p3.py lfm2vl_1.6b .*manifest_B.csv" >/dev/null; do sleep 15; done; echo "LB done $(date +%T)"
$PY run_p3.py lfm2vl_1.6b 8104 $S/manifest_P_lfm.csv P 448 n2 r0; echo "LP done $(date +%T)"
