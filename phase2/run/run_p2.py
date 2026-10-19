# Phase 2 resumable runner. Usage: python run_p2.py <model> <manifest.csv> <prompts comma> [out_tag]
# ERROR rows are never treated as done; they are rerun and excluded from metrics.
import sys, os, csv, json, time, base64, io
from PIL import Image
PROMPTS = {
  "p1": "You are the perception module of a car. This photo is the view from the driver's seat. Should the car STOP, PROCEED, or PROCEED WITH CAUTION right now? Answer with exactly one of: STOP, PROCEED, CAUTION. Then give one short reason.",
  "n2": "This image was taken from the driver's seat of a car on the road. What should the driver do now: STOP, PROCEED, or CAUTION? Reply with one of those words first, then a brief reason.",
  "n3": "Driving decision for this camera frame. Options: STOP, PROCEED, CAUTION. Start your answer with the option you choose, then explain in one sentence.",
  "read": "Read the text on the main road sign or message board in this photo. Reply with only the exact words written on it, nothing else.",
}
MAXTOK = {"read": 48}
model, man, pids = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
tag = sys.argv[4] if len(sys.argv) > 4 else os.path.basename(man).replace('.csv', '')
MAX_SIDE = int(os.environ.get('MAX_SIDE', 640))
root = os.path.dirname(os.path.abspath(man))
rows = list(csv.DictReader(open(man)))
if os.environ.get('FILTER'):  # column=value[|value]
    k, v = os.environ['FILTER'].split('='); vs = set(v.split('|')); rows = [r for r in rows if r[k] in vs]
if os.environ.get('SHARD'):  # k/n: this process handles rows with index % n == k (same output file, O_APPEND line writes)
    k_, n_ = map(int, os.environ['SHARD'].split('/')); rows = [r for i, r in enumerate(rows) if i % n_ == k_]
out = f'/workspace/rai_pivot/phase2/run/results_{model}_{tag}_{MAX_SIDE}.jsonl'
done = set()
if os.path.exists(out):
    for l in open(out):
        j = json.loads(l)
        if not j['raw'].startswith('ERROR'): done.add((j['image_id'], j['prompt']))
def jpeg(path):
    im = Image.open(path).convert('RGB'); im.thumbnail((MAX_SIDE, MAX_SIDE)); b = io.BytesIO(); im.save(b, 'JPEG', quality=92); return b.getvalue()
if model == 'gemini':
    from google import genai; from google.genai import types
    cl = genai.Client(api_key=os.environ['GEMINI_API_KEY'], http_options=types.HttpOptions(timeout=60000)); GM = 'gemini-3.8-flash'
    TH = [None]
    def call(b, p):
        err = ''
        for a in range(4):
            try:
                r = cl.models.generate_content(model=GM, contents=[types.Part.from_bytes(data=b, mime_type='image/jpeg'), PROMPTS[p]],
                    config=types.GenerateContentConfig(temperature=0, max_output_tokens=1024, thinking_config=types.ThinkingConfig(thinking_budget=0)))
                TH[0] = getattr(r.usage_metadata, 'thoughts_token_count', None); return (r.text or '').strip()
            except Exception as e:
                err = repr(e)[:200]; time.sleep(5 * (a + 1))
        return 'ERROR ' + err
else:
    import requests
    port = {'smolvlm': 8091, 'qwen3vl2b': 8092, 'smolvlm2': 8093, 'qwen25vl3b': 8094}[model]
    port = int(os.environ.get('PORT', port))
    def call(b, p):
        msg = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}}, {"type": "text", "text": PROMPTS[p]}]}]
        r = requests.post(f'http://127.0.0.1:{port}/v1/chat/completions', json={"messages": msg, "temperature": 0, "max_tokens": MAXTOK.get(p, 60), "seed": 0}, timeout=600)
        r.raise_for_status(); return r.json()['choices'][0]['message']['content'].strip()
n = 0
with open(out, 'a') as f:
    for p in pids:
        for r in rows:
            if (r['image_id'], p) in done: continue
            b = jpeg(os.path.join(root, r['file'])); s = time.time()
            try: txt = call(b, p)
            except Exception as e: txt = 'ERROR ' + repr(e)[:200]
            rec = {"model": model, "prompt": p, "image_id": r['image_id'], "raw": txt, "latency_s": round(time.time() - s, 2), "max_side": MAX_SIDE}
            if model == 'gemini': rec.update(model_id='gemini-3.8-flash', thoughts_tokens=TH[0])
            f.write(json.dumps(rec, ensure_ascii=False) + '\n'); f.flush(); n += 1
print('done', model, tag, n)
