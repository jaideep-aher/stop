#!/bin/bash
# after InternVL3 gate: stop its server, start LFM2-VL-1.6B (2 threads), run its gate at 448 (same as second-model resolution)
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd $ROOT/phase3/run
while pgrep -f chain_I.sh >/dev/null; do sleep 10; done
pkill -f "llama-server.*--port 8103"; sleep 3
cd $ROOT/bench; export LD_LIBRARY_PATH=$PWD/llama/llama-b11723
nohup llama/llama-b11723/llama-server -m models/LFM2-VL-1.6B-Q8_0.gguf --mmproj models/mmproj-LFM2-VL-1.6B-Q8_0.gguf -t 2 -c 8192 -np 1 --cache-ram 0 --port 8104 --host 127.0.0.1 > $ROOT/phase3/run/server_lfm2.log 2>&1 &
until curl -sf 127.0.0.1:8104/health >/dev/null; do sleep 2; done
cd $ROOT/phase3/run; PY=$ROOT/pilot/venv/bin/python; S=$ROOT/phase3/stimuli
$PY run_p3.py lfm2vl_1.6b 8104 $S/manifest_G1.csv G1 448 p1,n2,n3,L1,L2 r0; echo "LG1 done $(date +%T)"
$PY run_p3.py lfm2vl_1.6b 8104 $S/manifest_G2.csv G2 448 p1,n2,n3,L1,L2 r0; echo "LG2 done $(date +%T)"
