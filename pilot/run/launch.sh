#!/bin/bash
# (Re)start servers + resumable runners. Safe to rerun; runners skip finished (image_id,prompt) pairs.
cd /workspace/rai_pivot/bench; B=$PWD/llama/llama-b11723; export LD_LIBRARY_PATH=$B; R=/workspace/rai_pivot/pilot/run; P=/workspace/rai_pivot/pilot/venv/bin/python
pgrep -f "port 8091" >/dev/null || nohup $B/llama-server -m models/SmolVLM-500M-Instruct-Q8_0.gguf --mmproj models/mmproj-SmolVLM-500M-Instruct-Q8_0.gguf -t 2 -c 4096 -np 1 --port 8091 --host 127.0.0.1 >> $R/server_smol.log 2>&1 &
pgrep -f "port 8092" >/dev/null || nohup $B/llama-server -m models/Qwen3-VL-2B-Instruct-Q8_0.gguf --mmproj models/mmproj-Qwen3-VL-2B-Instruct-Q8_0.gguf -t 5 -c 4096 -np 1 --port 8092 --host 127.0.0.1 >> $R/server_qwen.log 2>&1 &
until curl -sf 127.0.0.1:8091/health >/dev/null && curl -sf 127.0.0.1:8092/health >/dev/null; do sleep 2; done
cd $R
pgrep -f "run_pilot.py smolvlm" >/dev/null || nohup $P run_pilot.py smolvlm p1,p2 >> log_smol.txt 2>&1 &
pgrep -f "run_pilot.py qwen3vl2b" >/dev/null || nohup $P run_pilot.py qwen3vl2b ${QWEN_PROMPTS:-p1} >> log_qwen.txt 2>&1 &
pgrep -f "run_pilot.py gemini" >/dev/null || nohup $P run_pilot.py gemini p1,p2 >> log_gem.txt 2>&1 &
echo launched
