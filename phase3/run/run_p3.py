# Phase 3 runner. Image-outer loop so llama-server reuses the image prefix across prompts/runs.
# Usage: python run_p3.py <model> <port> <manifest.csv> <arm_tag> <sides comma> <prompts comma> <runs comma>
# ERROR rows are never treated as done; retried up to 3x inline; leftovers rerun on restart and excluded from metrics.
import sys, os, csv, json, time, base64, io, requests
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'phase2', 'run'))
import re
src = open(os.path.join(ROOT, 'phase2', 'run', 'run_p2.py')).read()
PROMPTS = eval(src[src.index('PROMPTS = {') + len('PROMPTS = '): src.index('}\n', src.index('PROMPTS = {')) + 1])
PROMPTS['L1'] = ("This image is the view from the driver's seat of a car. Choose what the car should do right now. "
                 "A) come to a complete halt. B) keep driving normally. C) continue slowly and carefully. Answer with only the letter A, B, or C.")
PROMPTS['L2'] = ("This image is the view from the driver's seat of a car. Choose what the car should do right now. "
                 "A) keep driving normally. B) continue slowly and carefully. C) come to a complete halt. Answer with only the letter A, B, or C.")
RUNS = {'r0': dict(temperature=0, seed=0), 'r1': dict(temperature=0.7, top_p=0.8, top_k=20, seed=1), 'r2': dict(temperature=0.7, top_p=0.8, top_k=20, seed=2)}
model, port, man, arm, sides, pids, runs = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], [int(s) for s in sys.argv[5].split(',')], sys.argv[6].split(','), sys.argv[7].split(',')
MAXTOK = int(os.environ.get('MAXTOK', 8))
rows = list(csv.DictReader(open(man)))
if os.environ.get('FILTER'):
    k, v = os.environ['FILTER'].split('='); vs = set(v.split('|')); rows = [r for r in rows if r[k] in vs]
if os.environ.get('SHARD'):
    k_, n_ = map(int, os.environ['SHARD'].split('/')); rows = [r for i, r in enumerate(rows) if i % n_ == k_]
root = os.path.dirname(os.path.abspath(man))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'results_{model}_{arm}.jsonl')
done = set()
if os.path.exists(out):
    for l in open(out):
        j = json.loads(l)
        if not j['raw'].startswith('ERROR'): done.add((j['image_id'], j['prompt'], j['run'], j['max_side']))
def jpeg(path, s):
    im = Image.open(path).convert('RGB'); im.thumbnail((s, s)); b = io.BytesIO(); im.save(b, 'JPEG', quality=92); return b.getvalue()
def call(b64, p, rn):
    msg = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}, {"type": "text", "text": PROMPTS[p]}]}]
    r = requests.post(f'http://127.0.0.1:{port}/v1/chat/completions', json={"messages": msg, "max_tokens": MAXTOK, **RUNS[rn]}, timeout=900)
    r.raise_for_status(); j = r.json(); return j['choices'][0]['message']['content'].strip(), (j.get('usage') or {}).get('prompt_tokens_details', {}).get('cached_tokens')
n = 0
with open(out, 'a') as f:
    for r in rows:
        path = r['file'] if r['file'].startswith('/') else os.path.join(root, r['file'])
        for s in sides:
            todo = [(p, rn) for p in pids for rn in runs if (r['image_id'], p, rn, s) not in done]
            if not todo: continue
            b64 = base64.b64encode(jpeg(path, s)).decode()
            for p, rn in todo:
                t0 = time.time(); txt, ct = 'ERROR none', None
                for a in range(3):
                    try: txt, ct = call(b64, p, rn); break
                    except Exception as e: txt = 'ERROR ' + repr(e)[:200]; time.sleep(3 * (a + 1))
                rec = {"model": model, "arm": arm, "prompt": p, "run": rn, **{k: v for k, v in RUNS[rn].items()}, "max_side": s, "max_tokens": MAXTOK,
                       "image_id": r['image_id'], "raw": txt, "latency_s": round(time.time() - t0, 2), "cached_tokens": ct}
                f.write(json.dumps(rec, ensure_ascii=False) + '\n'); f.flush(); n += 1
print('done', model, arm, n)
