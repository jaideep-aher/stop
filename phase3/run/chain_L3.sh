#!/bin/bash
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd $ROOT/phase3/run; PY=$ROOT/pilot/venv/bin/python; S=$ROOT/phase3/stimuli
$PY run_p3.py lfm2vl_1.6b 8104 $S/manifest_B.csv B 448 n2 r0; echo "LB done $(date +%T)"
$PY run_p3.py lfm2vl_1.6b 8104 $S/manifest_P.csv P 448 n2 r0; echo "LP done $(date +%T)"
