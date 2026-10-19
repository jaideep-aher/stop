import requests, json, re, time
UA = {'User-Agent': 'rai-pivot-research/0.1 (Duke AIPI student project; contact jaideep.aher@duke.edu)'}
API = 'https://commons.wikimedia.org/w/api.php'
def q(**p):
    p['format'] = 'json'; return requests.get(API, params=p, headers=UA, timeout=60).json()
def catsearch(term):
    r = q(action='query', list='search', srsearch=term, srnamespace=14, srlimit=20)
    return [x['title'] for x in r['query']['search']]
cats = set()
for t in ['Billboard hacking', 'Subvertising', 'Modified road signs', 'Altered road signs', 'Vandalized road signs', 'Hacked variable message sign', 'Zombies ahead sign', 'Changeable message signs humor', 'Defaced road signs', 'Culture jamming', 'Road sign art', 'Graffiti on road signs', 'Stickers on road signs', 'Humorous road signs']:
    for c in catsearch(t): cats.add(c)
print(sorted(cats))
json.dump(sorted(cats), open('tamper_cats.json', 'w'), indent=0)
