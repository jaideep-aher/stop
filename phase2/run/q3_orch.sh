set -x
while pgrep -f "smol_chain" >/dev/null; do sleep 15; done
pkill -f "port 8091"; pkill -f q3_chain2.sh; pkill -f "run_p2.py qwen3vl2b"; sleep 3
cd /workspace/rai_pivot/bench; export LD_LIBRARY_PATH=$PWD/llama/llama-b11723
nohup llama/llama-b11723/llama-server -m models/Qwen3-VL-2B-Instruct-Q8_0.gguf --mmproj models/mmproj-Qwen3-VL-2B-Instruct-Q8_0.gguf -t 4 -c 4096 -np 1 --cache-ram 0 --port 8095 --host 127.0.0.1 >> /workspace/rai_pivot/phase2/run/server_qwen3b.log 2>&1 &
until curl -sf 127.0.0.1:8095/health >/dev/null; do sleep 2; done
cd /workspace/rai_pivot/phase2/run
( SHARD=0/2 FILTER=arm=en\|proceed_at_stop /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv p1 main
  FILTER=variant=benign\|inject_stop /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_en
  /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/real_manifest.csv p1 real
  SHARD=0/2 FILTER=arm=deva /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv p1 deva
  FILTER=block=G /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/pilot/v2work/pilot_v2/manifest.csv n2 gate
  /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest_wording2.csv n2 wording2 ) > log_q3A.txt 2>&1 &
( export PORT=8095
  SHARD=1/2 FILTER=arm=en\|proceed_at_stop /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv p1 main
  SHARD=1/2 FILTER=arm=deva /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv p1 deva
  FILTER=variant=hi_deva_1\|en_deva_1\|deva_benign\|latn_benign\|hi_latn_1 /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/phase2/stimuli/manifest.csv read read_deva
  FILTER=block=G /workspace/rai_pivot/pilot/venv/bin/python run_p2.py qwen3vl2b /workspace/rai_pivot/pilot/v2work/pilot_v2/manifest.csv n3 gate ) > log_q3B.txt 2>&1 &
wait
