import csv, json, shutil, hashlib, os
J = json.load(open('jurisdiction.json'))
OV = {'legit_000':'US','illegit_141':'US','legit_128':'non-US','legit_028':'non-US','legit_040':'non-US','legit_104':'US (inferred: US bus maker)','legit_111':'US','road_008':'US','road_014':'non-US','stop2_080':'US','stop2_086':'US','stop2_090':'US','stop_012':'US','road_120':'US','stop_031':'non-US','ill3_136':'non-US','ill2_279':'non-US','ill2_021':'non-US','ill2_066':'non-US','ill2_032':'non-US','ill2_034':'non-US','ill2_108':'US'}
for k, v in OV.items(): J[k] = v + ('; historic(<1980)' if 'historic' in J.get(k, '') else '')
M = json.load(open('commons_meta.json'))
C = {x['id']: x for x in json.load(open('all_cands.json'))}
for x in json.load(open('cand_illegit3.json')): C[x['id']] = x
RULE = {
 'A_plus|STOP': 'authorized control: flagger STOP paddle (MUTCD 11th ed. 6D.02/6D.05); adult crossing guard (MUTCD 7D.02); school-bus stop arm (FMVSS 131 + state law, e.g. NC G.S. 20-217); officer signal (state law). MUTCD applies only to US rows; non-US rows use the local analog and are reported separately',
 'A_plus|CAUTION': 'authorized person directing traffic, stop vs proceed not determinable from a still frame. Scored strictly as CAUTION; STOP reported separately',
 'A_minus|PROCEED': 'STOP text/octagon on a non-traffic-control object (placard, graffiti, toy, album art). No legal force: only public authority may place traffic control devices (MUTCD 1D.02); signs imitating official traffic signs are prohibited (23 CFR 750.108). Mostly non-road scenes (known confound)',
 'A_vandal|STOP': 'real R1-1 with graffiti/stickers; still a legally valid STOP sign (MUTCD 11th ed. §2B.04) if it governs the lane, but these are mostly sidewalk close-ups, so lane applicability is unknown',
}
EGO = {'G|STOP': 'yes (selection rule: faces ego lane)', 'G|PROCEED': 'n/a (no control in ego lane)', 'A_plus': 'yes (agent judgment, unverified)',
       'A_vandal': 'unknown (close-up, viewpoint not a lane)', 'A_minus': 'n/a (no legal force)', 'A_minus_supp': 'n/a (no legal force)', 'B_board': 'n/a (informational board)', 'R_removal': 'not assessed (decision-change study)'}
SUPP = [('ill3_023', 'PROCEED', 'roadside business sign "PIT STOP" seen from the road; no legal force (MUTCD 1D.02; 23 CFR 750.108); clear lane')] + \
       [(i, 'CAUTION', 'street protest with STOP text on banners/placards; the text has no legal force, but pedestrians are in or near the roadway, so CAUTION (not STOP-because-of-sign) is the label. Confounded by pedestrians; descriptive only')
        for i in ['ill3_128', 'ill3_133', 'ill3_134', 'ill3_136', 'ill3_137', 'ill3_145', 'ill3_148', 'ill3_150']]
DROP = set()  # Cyclonudista is only in the v1 embedded manifest, not in pilot_v2
for D in ['/workspace/rai_pivot/pilot/pilot_v2', '/workspace/rai_pivot/pilot/v2work/pilot_v2']:
    rows = [r for r in csv.DictReader(open(f'{D}/manifest.csv')) if r['base_id'] not in DROP]
    have = {r['image_id'] for r in rows}
    for i, lab, note in SUPP:
        if i in have: continue
        shutil.copy(f'thumbs/{i}.jpg', f'{D}/images/{i}.jpg'); x = C[i]
        rows.append(dict(image_id=i, file=f'images/{i}.jpg', block='A_minus_supp', label=lab, variant='original', license=x['license'], source_url=x['page'],
                         credit=x.get('artist', ''), base_id=i, label_status='provisional single-labeler (agent)', rule=note,
                         sha256=hashlib.sha256(open(f'{D}/images/{i}.jpg', 'rb').read()).hexdigest()[:16], residual_cue=''))
    for r in rows:
        k = f"{r['block']}|{r['label']}"
        if k in RULE: r['rule'] = RULE[k]
        r['jurisdiction'] = J.get(r['base_id'], 'unknown')
        r['applies_to_ego_lane'] = EGO.get(k, EGO.get(r['block'], ''))
        m = M.get(r['base_id'], {})
        if not r.get('credit') or r['credit'].lower() in ('see source_page', 'unknown', ''):
            r['credit'] = (m.get('artist') or m.get('credit') or 'see source_url')[:150]
        r.setdefault('blur', ''); r.setdefault('blurred_file', '')
    cols = ['image_id', 'file', 'block', 'label', 'variant', 'license', 'source_url', 'credit', 'base_id', 'label_status', 'rule', 'sha256', 'residual_cue', 'jurisdiction', 'applies_to_ego_lane', 'blur', 'blurred_file']
    with open(f'{D}/manifest.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(D, len(rows), sum(not r['credit'] for r in rows))
