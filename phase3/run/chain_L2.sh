#!/bin/bash
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd $ROOT/phase3/run; PY=$ROOT/pilot/venv/bin/python; S=$ROOT/phase3/stimuli
$PY run_p3.py lfm2vl_1.6b 8104 $S/manifest_G1.csv G1 448 p1,n2,n3 r0; echo "LG1 done $(date +%T)"
$PY run_p3.py lfm2vl_1.6b 8104 $S/manifest_G2.csv G2 448 p1,n2,n3 r0; echo "LG2 done $(date +%T)"
