import json, re
M = json.load(open('commons_meta.json'))
C = {x['id']: x for x in json.load(open('all_cands.json'))}
for x in json.load(open('cand_illegit3.json')): C[x['id']] = x
STATES = "Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia \(U\.?S|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington, D\.?C|Washington \(state\)|West Virginia|Wisconsin|Wyoming|United States|\bUSA\b|\bU\.S\.|San Francisco|Los Angeles|Chicago|Seattle|Boston|Brooklyn|Manhattan|Philadelphia|Portland, Oregon|Denver|Atlanta|Houston|Austin|Durham|Raleigh|Charlotte|Puerto Rico|Interstate \d|U\.S\. Route|Honolulu|Kaneohe|Minneapolis|Pittsburgh|Baltimore|Detroit|Cleveland|Miami|Orlando|Tampa|Nashville|Memphis|Huntsville|Montgomery|Birmingham, Alabama|Phoenix|Tucson|Las Vegas|Sacramento|San Diego|San Jose|Oakland|Berkeley|Cincinnati|Columbus, Ohio|Milwaukee|Madison, Wisconsin|St\. Louis|Kansas City|Omaha|Salt Lake|Albuquerque|Anchorage|Fort Lauderdale|Sawgrass|Bowling Green|Briley|Gadsden|Decatur"
NONUS = "Canada|Ontario|Quebec|Québec|Toronto|Montreal|Vancouver|Mexico|United Kingdom|England|Scotland|Wales|London|Ireland|Germany|Deutschland|France|Paris|Spain|Portugal|Italy|Netherlands|Belgium|Switzerland|Austria|Poland|Czech|Prague|Praha|Slovakia|Hungary|Romania|Bulgaria|Greece|Turkey|Russia|Ukraine|Україн|Belarus|Lithuania|Latvia|Estonia|Finland|Sweden|Norway|Denmark|Iceland|Croatia|Serbia|Slovenia|Bosnia|Montenegro|Macedonia|Albania|Israel|Lebanon|Iran|India|Pakistan|Bangladesh|Sri Lanka|Nepal|China|Hong Kong|Taiwan|Japan|Korea|Philippines|Vietnam|Thailand|Malaysia|Singapore|Indonesia|Australia|New Zealand|Brazil|Argentina|Chile|Peru|Colombia|Venezuela|South Africa|Kenya|Nigeria|Egypt|Morocco|Uzbekistan|Kazakhstan|Georgia \(country\)|Armenia|Cyprus|Malta|Luxembourg|Tbilisi|Sydney|Melbourne|Brisbane|Perth|Adelaide|Auckland|Wellington|Berlin|Munich|Hamburg|Vienna|Zurich|Geneva|Amsterdam|Brussels|Madrid|Barcelona|Lisbon|Rome|Milan|Athens|Istanbul|Warsaw|Kraków|Budapest|Bucharest|Sofia|Kyiv|Kiev|Moscow|Tokyo|Seoul|Beijing|Shanghai|Taipei|Manila|Bangkok|Jakarta|Delhi|Mumbai|Dublin|Edinburgh|Glasgow|Cardiff|Manchester|Liverpool|Oslo|Stockholm|Helsinki|Copenhagen|geograph\.org\.uk|Tasmania|Launceston|Victoria \(Australia\)|New South Wales|Queensland|Pálkäne|Pälkäne|Lviv|Ambassador Bridge|Rhodes|Ródos"
def classify(b):
    m = M.get(b, {}); t = C[b]['title']
    blob = ' | '.join([t] + m.get('cats', []) + [m.get('desc', '')])
    yrs = [int(y) for y in re.findall(r'\b(1[89]\d\d|20[0-2]\d)\b', m.get('date', '') + ' ' + t)]
    hist = bool(yrs) and min(yrs) < 1980
    us, non = bool(re.search(STATES, blob)), bool(re.search(NONUS, blob, re.I))
    j = 'US' if us and not non else 'non-US' if non and not us else 'mixed-check' if us and non else 'unknown'
    return j + ('; historic(<1980)' if hist else ''), blob
if __name__ == '__main__':
    from collections import Counter
    res = {b: classify(b)[0] for b in M}; json.dump(res, open('jurisdiction.json', 'w'), indent=0)
    print(Counter(v.split(';')[0] for v in res.values()))
    for b in res:
        if res[b].startswith(('unknown', 'mixed')): print(b, res[b], classify(b)[1][:160])
