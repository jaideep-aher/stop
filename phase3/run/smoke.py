# Engineering smoke test on bench/imgs (NOT study stimuli): latency + prefix-cache behaviour.
import requests, base64, io, time, sys
from PIL import Image
port=int(sys.argv[1]); img=sys.argv[2]
def jpeg(p,s):
    im=Image.open(p).convert('RGB'); im.thumbnail((s,s)); b=io.BytesIO(); im.save(b,'JPEG',quality=92); return b.getvalue()
for s in (448,640,896):
    b=base64.b64encode(jpeg(img,s)).decode()
    for txt,T,seed in [("Should the car STOP, PROCEED or CAUTION? One word.",0,0),("Driving decision: STOP, PROCEED, CAUTION. Start with the option.",0,0),("Driving decision: STOP, PROCEED, CAUTION. Start with the option.",0.7,1),("Driving decision: STOP, PROCEED, CAUTION. Start with the option.",0,0)]:
        t=time.time()
        r=requests.post(f'http://127.0.0.1:{port}/v1/chat/completions',json={"messages":[{"role":"user","content":[{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+b}},{"type":"text","text":txt}]}],"temperature":T,"seed":seed,"max_tokens":8}).json()
        print(s,T,seed,round(time.time()-t,2),repr(r['choices'][0]['message']['content']),r.get('usage'),r.get('timings',{}).get('prompt_n'))
