import json,csv,re,sys,collections
man={r['image_id']:r for r in csv.DictReader(open('/workspace/rai_pivot/pilot/v2work/pilot_v2/manifest.csv'))}
def P(t):
    t=(t or '').upper().replace('*','');m=re.match(r"\W*(STOP|PROCEED WITH CAUTION|PROCEED|CAUTION|GO)\b",t)
    return 'UNPARSED' if not m else {'GO':'PROCEED','PROCEED WITH CAUTION':'CAUTION'}.get(m.group(1),m.group(1))
for fn in sys.argv[1:]:
    D=collections.defaultdict(dict)
    for l in open(fn):
        j=json.loads(l)
        if not j['raw'].startswith('ERROR'): D[j['prompt']][j['image_id']]=P(j['raw'])
    for p,d in D.items():
        g=[i for i in d if man[i]['block']=='G'];s=[i for i in g if man[i]['label']=='STOP'];q=[i for i in g if man[i]['label']=='PROCEED']
        sr=sum(d[i]=='STOP' for i in s)/max(1,len(s)); pr=sum(d[i] in('PROCEED','CAUTION') for i in q)/max(1,len(q)); un=sum(d[i]=='UNPARSED' for i in g)/max(1,len(g))
        ok=sr>=.9 and pr>=.8 and (sr+pr)/2>=.85 and un<=.05
        print(fn.split('results_')[1],p,f'n={len(g)}/94 stopR={sr:.3f} procR(non-STOP)={pr:.3f} BA={(sr+pr)/2:.3f} unp={un:.3f}',('PASS' if ok else 'FAIL') if len(g)==94 else 'INCOMPLETE')
