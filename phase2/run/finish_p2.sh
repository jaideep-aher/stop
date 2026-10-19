# Bounded finish (worker 03:15 ET): wait for qwen main shards, then qwen read_en (sharded on both servers) + real; then smol rerun of error rows.
set -x
PY=/workspace/rai_pivot/pilot/venv/bin/python; M=/workspace/rai_pivot/phase2/stimuli/manifest.csv
cd /workspace/rai_pivot/phase2/run
while kill -0 130047 2>/dev/null || kill -0 130048 2>/dev/null; do sleep 10; done
( SHARD=0/2 FILTER=variant=benign\|inject_stop $PY run_p2.py qwen3vl2b $M read read_en
  $PY run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/real_manifest.csv p1 real ) &
( PORT=8095 SHARD=1/2 FILTER=variant=benign\|inject_stop $PY run_p2.py qwen3vl2b $M read read_en ) &
wait
kill 111198 129944; sleep 3
cd /workspace/rai_pivot/bench; export LD_LIBRARY_PATH=$PWD/llama/llama-b11723
nohup llama/llama-b11723/llama-server -m models/SmolVLM-500M-Instruct-Q8_0.gguf --mmproj models/mmproj-SmolVLM-500M-Instruct-Q8_0.gguf -t 8 -c 4096 -np 1 --cache-ram 0 --port 8091 --host 127.0.0.1 >> /workspace/rai_pivot/phase2/run/server_smol.log 2>&1 &
until curl -sf 127.0.0.1:8091/health >/dev/null; do sleep 2; done
cd /workspace/rai_pivot/phase2/run
FILTER=arm=en\|proceed_at_stop $PY run_p2.py smolvlm $M p1 main
$PY run_p2.py smolvlm /workspace/rai_pivot/phase2/stimuli/real_manifest.csv p1 real
FILTER=variant=benign\|inject_stop $PY run_p2.py smolvlm $M read read_en
echo FINISHED
