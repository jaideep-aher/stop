import json,sys,os
F='selections.json'
d=json.load(open(F)) if os.path.exists(F) else {}
k=sys.argv[1]; ids=sys.argv[2].split(',')
d.setdefault(k,[]); [d[k].append(i) for i in ids if i not in d[k]]
json.dump(d,open(F,'w'),indent=0); print({a:len(b) for a,b in d.items()})
