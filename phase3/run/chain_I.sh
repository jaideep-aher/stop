#!/bin/bash
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=$ROOT/pilot/venv/bin/python; S=$ROOT/phase3/stimuli
cd $ROOT/phase3/run
$PY run_p3.py internvl3_2b 8103 $S/manifest_G1.csv G1 448 p1,n2,n3,L1,L2 r0; echo "G1 done $(date +%T)"
$PY run_p3.py internvl3_2b 8103 $S/manifest_G2.csv G2 448 p1,n2,n3,L1,L2 r0; echo "G2 done $(date +%T)"
