#!/bin/bash
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=$ROOT/pilot/venv/bin/python; S=$ROOT/phase3/stimuli
cd $ROOT/phase3/run
two(){ SHARD=0/2 $PY run_p3.py qwen3vl2b 8101 $1 ${2}_s0 $3 $4 $5 & SHARD=1/2 $PY run_p3.py qwen3vl2b 8102 $1 ${2}_s1 $3 $4 $5 & wait; echo "$2 $3 done $(date +%T)"; }
two $S/manifest_R.csv R 640 p1,n2,n3,L1,L2 r0,r1,r2
two $S/manifest_G1.csv G1 448,640,896 p1,n2,n3,L1,L2 r0
two $S/manifest_G2.csv G2 448,640,896 p1,n2,n3,L1,L2 r0
two $S/manifest_P.csv P 640 p1,n2,n3,L1,L2 r0
two $S/manifest_R.csv R 448 p1,n2,n3,L1,L2 r0,r1,r2
two $S/manifest_R.csv R 896 p1,n2,n3,L1,L2 r0,r1,r2
echo ALLDONE
