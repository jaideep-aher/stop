#!/bin/bash
# R arm: 3 passes (640, 448, 896), 2 shards on 2 servers. 15 conditions per image per side.
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PY=$ROOT/pilot/venv/bin/python; M=$ROOT/phase3/stimuli/manifest_R.csv
cd $ROOT/phase3/run
for S in 640 448 896; do
  SHARD=0/2 $PY run_p3.py qwen3vl2b 8101 $M R_s0 $S p1,n2,n3,L1,L2 r0,r1,r2 &
  SHARD=1/2 $PY run_p3.py qwen3vl2b 8102 $M R_s1 $S p1,n2,n3,L1,L2 r0,r1,r2 &
  wait; echo "pass $S done $(date +%T)"
done
