#!/bin/sh
# One-command rebuild: detector blur (cached YOLO boxes reused) -> site data -> optional serve.
#   ./rebuild.sh            blur + build
#   ./rebuild.sh --fresh    also re-run YOLO (delete cached boxes), e.g. after new stimuli
#   ./rebuild.sh --serve    blur + build, then (re)serve site on http://127.0.0.1:8765
set -e; cd "$(dirname "$0")"
case " $* " in *" --fresh "*) rm -f blur_inputs/boxes_*.json;; esac
sh run_blur.sh
python3 site/build_site_data.py
case " $* " in *" --serve "*) pkill -f "http.server 8765" || true
  (cd site && nohup python3 -m http.server 8765 --bind 127.0.0.1 >/tmp/site_http.log 2>&1 &); echo "serving http://127.0.0.1:8765";; esac
