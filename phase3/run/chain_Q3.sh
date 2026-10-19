#!/bin/bash
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=$ROOT/pilot/venv/bin/python; S=$ROOT/phase3/stimuli; cd $ROOT/phase3/run
while pgrep -f "run_p3.py qwen3vl2b .*manifest_P.csv" >/dev/null; do sleep 15; done; echo "P done $(date +%T)"
two(){ SHARD=0/2 $PY run_p3.py qwen3vl2b 8101 $1 ${2}_s0 $3 $4 $5 & SHARD=1/2 $PY run_p3.py qwen3vl2b 8102 $1 ${2}_s1 $3 $4 $5 & wait; echo "$2 $3 done $(date +%T)"; }
two $S/manifest_R.csv R 448 p1,n2,n3,L1,L2 r0,r1,r2
two $S/manifest_R896sub.csv R 896 p1,n2,n3,L1,L2 r0,r1,r2
echo ALLDONE
