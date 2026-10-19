#!/usr/bin/env python3
"""Build site/data/data.json for "Who Gets to Say STOP?" (Phase 2 board study first, pilot as background).

READ-ONLY inputs (never written):
  phase2/analysis/phase2_metrics.json   SOURCE OF TRUTH for every Phase 2 number
  phase2/run/results_{qwen3vl2b,gemini,smolvlm}_main_640.jsonl   per-image decisions (board + PROCEED-at-STOP arms)
  phase2/stimuli/{manifest,real_manifest}.csv, analysis/examples_spec.json (pair ids only)
  phase2/fig1_board_stop_rates.png, phase2/fig2_proceed_at_stop_and_script.png (left panel only)
  pilot/run/pilot_metrics.json, pilot/pilot_v2/manifest.csv (+ blurred/)
Never reads phase2/private/. Never emits legend text per image, and nothing is ranked by effect.
Publication rule: an image is copied only if it has a license, a credit and a blurred copy (Phase 2: site-side sidecar data/phase2_blur.csv,
written by ../blur_detect.py, 'detector-based, unverified'); pilot images pending plate review stay withheld; unblurred originals are never published.
Usage: python build_site_data.py [--root REPO_ROOT]
The default root is this repository (two levels above this file)."""
import csv, json, os, re, sys, shutil, glob, datetime
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = sys.argv[sys.argv.index('--root') + 1] if '--root' in sys.argv else REPO
P2 = f'{ROOT}/phase2'; PIL_ = f'{ROOT}/pilot'
OUT = f'{HERE}/data'; IMG = f'{OUT}/img'
MODELS = {'qwen3vl2b': 'Qwen3-VL-2B (on-device class)', 'gemini': 'Gemini Flash (frontier reference)', 'smolvlm': 'SmolVLM-500M (failed stop-sign gate)'}
BOARD_VARIANTS = [  # fixed design order (never sorted by effect)
 ('clean', 'Clean (no edit)'), ('benign', 'Benign edit (place name / road work)'), ('official', 'Official text (ROAD CLOSED)'),
 ('inject_stop', 'Injection (imperative stop command)'), ('benign_cmd', 'Length-matched benign command'),
 ('nonsense', 'Length-matched nonsense'), ('bare_stop', 'Bare "STOP"'), ('bb_inject_stop', 'Billboard twin: injection'),
 ('bb_benign_cmd', 'Billboard twin: benign command')]
STOP_VARIANTS = [('sclean', 'Real STOP scene, no board'), ('sboard_benign', '+ benign message board'), ('sboard_proceed', '+ PROCEED-at-STOP board')]
EXCLUDE = re.compile(r'cyclonudista', re.I)

def _hard_exclude():
    """Load the public hard-exclude list. It lives outside this web root so the ids are not published."""
    import importlib.util
    path = os.path.join(os.path.dirname(HERE), 'build_pages_artifact.py')
    spec = importlib.util.spec_from_file_location('pages_builder', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.HARD_EXCLUDE_IDS, mod.HARD_EXCLUDE_URLS

def parse_action(t):  # strict leading-word parser, same as the project analyzers
    t = (t or '').upper().replace('*', '')
    m = re.match(r"\W*(STOP|PROCEED WITH CAUTION|PROCEED|CAUTION|GO)\b", t)
    return 'UNPARSED' if not m else {'GO': 'PROCEED', 'PROCEED WITH CAUTION': 'CAUTION'}.get(m.group(1), m.group(1))

def thumb(src, dst, side=480):
    im = Image.open(src).convert('RGB'); im.thumbnail((side, side)); im.save(dst, 'JPEG', quality=85)

def main():
    shutil.rmtree(IMG, ignore_errors=True); os.makedirs(f'{IMG}/pilot', exist_ok=True); os.makedirs(f'{IMG}/p2', exist_ok=True)
    M = json.load(open(f'{P2}/analysis/phase2_metrics.json'))

    # ---------- Phase 2 stimuli (metadata only; no per-image blur record => image withheld) ----------
    man = list(csv.DictReader(open(f'{P2}/stimuli/manifest.csv', newline='')))
    main_rows = [r for r in man if r['set'] == 'board' and r['arm'] == 'en' or r['set'] == 'stopscene']
    bases = {}
    for r in main_rows:
        b = bases.setdefault(r['base_id'], {'base_id': r['base_id'], 'arm': 'board' if r['set'] == 'board' else 'proceed_at_stop',
             'board_type': r['board_type'] or None, 'cluster_id': r['cluster_id'], 'credit': r['credit'], 'license': r['license'],
             'source_url': r['source_url'], 'label': r['label'] if r['variant'] in ('clean', 'sclean') else None, 'images': {}})
        b['images'][r['variant']] = {'id': r['image_id'], 'edited': r['edited'].startswith('yes'), 'label': r['label']}
    # decisions
    dec = {}; idset = {r['image_id'] for r in main_rows}; rowcount = {}
    for m in MODELS:
        fn = f'{P2}/run/results_{m}_main_640.jsonl'
        sp = M[m]['scored_prompt']; rowcount[m] = 0
        for line in open(fn):
            j = json.loads(line)
            if j['image_id'] not in idset or j['prompt'] != sp: continue
            err = j['raw'].startswith('ERROR')
            if err and dec.get(j['image_id'], {}).get(m): continue  # keep the valid (rerun) row
            dec.setdefault(j['image_id'], {})[m] = {'a': 'ERROR' if err else parse_action(j['raw'])}  # verdict only: reasons can quote edited board text
            rowcount[m] += 1
    for m in MODELS: rowcount[m] = sum(1 for d in dec.values() if m in d and d[m]['a'] != 'ERROR')
    SITE = os.path.dirname(HERE)  # site/ (blurred copies live in site/blurred)
    def sidecar(fn):
        return {r['image_id']: r for r in csv.DictReader(open(fn))} if os.path.exists(fn) else {}
    p2blur = sidecar(f'{OUT}/phase2_blur.csv'); realblur = sidecar(f'{OUT}/phase2_real_blur.csv')
    os.makedirs(f'{IMG}/p2/stim', exist_ok=True); os.makedirs(f'{IMG}/p2/real', exist_ok=True)
    p2_refusal = {'no_license': 0, 'no_credit': 0, 'no_blurred_copy': 0, 'pending_human_check': 0}
    def publish(rec, side, sub):
        why = []
        if not rec['license'].strip(): why.append('no_license')
        if not rec['credit'].strip(): why.append('no_credit')
        b = side.get(rec['image_id']); src = f"{SITE}/{b['blurred_file']}" if b and b['blurred_file'] else None
        if not src or not os.path.exists(src): why.append('no_blurred_copy')
        elif b['blur_status'].startswith('no_detections'): why.append('pending_human_check')  # unblurred re-encode = unverified original
        if why: return None, why, None
        t = f"data/img/p2/{sub}/{rec['image_id']}.jpg"; thumb(src, f'{HERE}/{t}')
        return t, [], b['blur_status']
    for r in main_rows:
        t, why, st = publish(r, p2blur, 'stim')
        for x in why: p2_refusal[x] += 1
        im = bases[r['base_id']]['images'][r['variant']]; im.update({'thumb': t, 'refusal': why, 'blur': st})
    real = []
    for r in csv.DictReader(open(f'{P2}/stimuli/real_manifest.csv', newline='')):
        t, why, st = publish(r, realblur, 'real')
        real.append({'id': r['image_id'], 'label': r['label'], 'credit': r['credit'], 'license': r['license'], 'source_url': r['source_url'],
                     'thumb': t, 'refusal': why, 'blur': st, 'edited': False})

    # ---------- Phase 2 examples: rebuilt from our blurred stimuli (no burned-in model text); spec pairs 1-5 only ----------
    spec = json.load(open(f'{P2}/analysis/examples_spec.json'))
    byid = {r['image_id']: r for r in man}; varlab = dict(BOARD_VARIANTS + STOP_VARIANTS)
    examples = []
    def flagged(iid): return (p2blur.get(iid) or {}).get('needs_human_check', 'yes') != 'no'
    def pair_ok(ids): return all(bases[byid[x]['base_id']]['images'][byid[x]['variant']].get('thumb') and not flagged(x) for x in ids)
    used = {byid[x]['base_id'] for i, sp in enumerate(spec, 1) if i <= 5 for x in sp.get('ids', []) if x in byid}  # never reuse a spec base
    for i, sp in enumerate(spec, 1):
        ids = list(sp.get('ids', [])); m = sp['model']; note = None
        if i > 5 or any(byid.get(x, {}).get('arm') == 'deva' for x in ids): continue  # never pair 6 / script arm
        recs = [byid[x] for x in ids]
        if not pair_ok(ids):
            # Substitute: same two conditions, same model, same verdict pattern as the spec pair, first unflagged base in id order
            # (deterministic; NOT chosen by effectiveness). Only bases whose images need no human check are eligible.
            vs = [r['variant'] for r in recs]; want = [dec.get(x, {}).get(m, {}).get('a') for x in ids]
            for bid in sorted(bases):
                im = bases[bid]['images']
                if bid in used or not all(v in im for v in vs): continue
                cand = [im[v]['id'] for v in vs]
                if pair_ok(cand) and [dec.get(x, {}).get(m, {}).get('a') for x in cand] == want:
                    why_ = sorted({(p2blur.get(x) or {}).get('check_reason', 'no blurred copy') for x in ids if flagged(x)}); note = f"substitute for spec pair {i} ({' / '.join(ids)} flagged: {'; '.join(why_)})"; ids = cand; break
            else: continue
            recs = [byid[x] for x in ids]
        used.add(recs[0]['base_id'])
        thumbs = [bases[r['base_id']]['images'][r['variant']].get('thumb') for r in recs]
        a, b = [Image.open(f'{HERE}/{t}').convert('RGB') for t in thumbs]; H = 360
        a = a.resize((int(a.width * H / a.height), H)); b = b.resize((int(b.width * H / b.height), H))
        c = Image.new('RGB', (a.width + b.width + 12, H), 'white'); c.paste(a, (0, 0)); c.paste(b, (a.width + 12, 0))
        fn = f'data/img/p2/example_{i}.jpg'; c.save(f'{HERE}/{fn}', quality=85)
        side = [{'condition': varlab[r['variant']], 'label': r['label'], 'verdict': dec.get(r['image_id'], {}).get(m, {}).get('a')} for r in recs]
        examples.append({'file': fn, 'model': m, 'sides': side, 'ids': ids, 'spec_pair': i, 'note': note, 'credit': recs[0]['credit'], 'license': recs[0]['license'],
                         'source_url': recs[0]['source_url'], 'edited': True, 'blur': 'detector-based, unverified'})
    # combined needs-human-check list for Jay (flagged blur sidecar rows + withheld pending-check images)
    nhc = []
    for set_, fn in (('phase2', 'phase2_blur.csv'), ('phase2_real', 'phase2_real_blur.csv'), ('pilot', 'pilot_notneeded_blur.csv')):
        for r in sidecar(f'{OUT}/{fn}').values():
            if r.get('needs_human_check') == 'yes':
                nhc.append([set_, r['image_id'], 'withheld' if r['blur_status'].startswith('no_detections') else 'published (blurred, extra blur kept)', r['check_reason'], r['blurred_file'], r['source_file']])
    with open(f'{OUT}/needs_human_check.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['set', 'image_id', 'site_status', 'reason', 'blurred_file', 'source_file']); w.writerows(nhc)
    # figures: fig1 as is (aggregated by condition); fig2 left panel only (script arm cropped out)
    shutil.copy(f'{P2}/fig1_board_stop_rates.png', f'{IMG}/p2/fig1.png')
    im = Image.open(f'{P2}/fig2_proceed_at_stop_and_script.png'); w, h = im.size
    im.crop((0, 45, 792, h)).save(f'{IMG}/p2/fig2_left.png')  # left panel frame ends at x=788 in the 1950-px source

    # ---------- Phase 2 metrics (copied verbatim, minus the exploratory script arm) ----------
    p2m = {}
    for m in MODELS:
        o = {k: v for k, v in M[m].items() if not k.startswith('deva')}
        p2m[m] = o

    # ---------- Pilot (background) ----------
    pman = list(csv.DictReader(open(f'{PIL_}/pilot_v2/manifest.csv', newline='')))
    pref = {'no_license': 0, 'no_credit': 0, 'no_blur_record': 0, 'plate_review_pending': 0, 'pending_human_check': 0, 'no_blurred_copy': 0, 'excluded_by_decision': 0}
    pimgs = []
    pnn = {r['image_id']: r for r in csv.DictReader(open(f'{OUT}/pilot_notneeded_blur.csv'))} if os.path.exists(f'{OUT}/pilot_notneeded_blur.csv') else {}
    skip_ids, skip_urls = _hard_exclude()
    for r in pman:
        if r['image_id'] in skip_ids or (r.get('source_url') or '') in skip_urls:
            continue
        why = []
        blur = r.get('blur', '').strip()
        if EXCLUDE.search(r['source_url'] + r['file']): why.append('excluded_by_decision')
        if not r['license'].strip(): why.append('no_license')
        if not r['credit'].strip(): why.append('no_credit')
        if not blur: why.append('no_blur_record')
        if 'MANUAL REVIEW' in blur.upper(): why.append('plate_review_pending')
        src = None
        if blur.startswith('blurred'):
            src = f"{PIL_}/pilot_v2/{r['blurred_file']}" if r['blurred_file'] else None
            if not src or not os.path.exists(src): why.append('no_blurred_copy')
        elif blur.startswith('not_needed'):
            # never publish an unverified unblurred original: use our detector-blurred copy instead
            b = pnn.get(r['image_id']); src = f"{os.path.dirname(HERE)}/{b['blurred_file']}" if b and b['blurred_file'] else None
            if not src or not os.path.exists(src): why.append('no_blurred_copy')
            elif b['blur_status'].startswith('no_detections'): why.append('pending_human_check')
            else: blur = b['blur_status'] + '; upstream: ' + blur
        for x in why: pref[x] += 1
        t = None
        if not why:
            t = f"data/img/pilot/{r['image_id']}.jpg"; thumb(src, f'{HERE}/{t}')
        pimgs.append({'id': r['image_id'], 'block': r['block'], 'label': r['label'], 'variant': r['variant'],
                      'edited': r['rule'].upper().startswith('DIGITALLY EDITED') or r['variant'] in ('sign_removed', 'control_removed') or (r['block'] == 'B_board' and r['variant'] != 'clean'),
                      'license': r['license'], 'credit': r['credit'], 'source_url': r['source_url'], 'jurisdiction': r.get('jurisdiction'),
                      'blur': blur, 'published': not why, 'refusal': why, 'thumb': t})
    pm = json.load(open(f'{PIL_}/run/pilot_metrics.json'))
    pm_slim = {k: {kk: v[kk] for kk in ('n_rows', 'gate', 'study1', 'median_latency_s') if kk in v} for k, v in pm.items()}

    data = {'generated_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
            'label_note': 'Labels are provisional, single labeler (an AI agent); no human rater yet. All edits are digital composites on real photos.',
            'models': MODELS, 'board_variants': BOARD_VARIANTS, 'stop_variants': STOP_VARIANTS,
            'p2': {'metrics': p2m, 'gate': M['_gate'], 'wording2': M['wording2'], 'gemini_model_id': M['_gemini_model_id'],
                   'gemini_calls': M['_gemini_phase2_calls'], 'bases': list(bases.values()), 'decisions': dec, 'rows_used': rowcount,
                   'refusals': p2_refusal, 'examples': examples, 'real': real,
                   'n_published': sum(1 for b in bases.values() for im in b['images'].values() if im.get('thumb')), 'n_stimuli': len(main_rows), 'figs': {'fig1': 'data/img/p2/fig1.png', 'fig2': 'data/img/p2/fig2_left.png'}},
            'pilot': {'metrics': pm_slim, 'images': pimgs, 'refusals': pref, 'n_published': sum(i['published'] for i in pimgs)},
            'repo': {'name': 'jaideep-aher/stop', 'status': 'private repository; GitHub Pages publishes only the filtered allowlist'}}
    # extra phases (e.g. Phase 3 robustness): listed in site/phases.json; missing metrics => honest empty state
    data['phases'] = []
    pj = f'{HERE}/phases.json'
    for ph in (json.load(open(pj)) if os.path.exists(pj) else []):
        mp = ph['metrics'] if os.path.isabs(ph['metrics']) else f"{ROOT}/{ph['metrics']}"
        ent = {k: ph.get(k) for k in ('id', 'title', 'blurb')}
        if os.path.exists(mp):
            ent['metrics'] = json.load(open(mp)); ent['source'] = os.path.relpath(mp, ROOT)
        else: ent['metrics'] = None; ent['source'] = os.path.relpath(mp, ROOT)
        data['phases'].append(ent)
    json.dump(data, open(f'{OUT}/data.json', 'w'), separators=(',', ':'))
    print(f"Phase 2: {len(bases)} bases, {len(main_rows)} stimuli, {data['p2']['n_published']} published, refusals {p2_refusal}; real tampered {sum(1 for x in real if x['thumb'])}/{len(real)} published; {len(examples)} example pairs; rows used {rowcount}")
    print(f"Needs human check: {len(nhc)} rows -> data/needs_human_check.csv; phases: {[(p['id'], p['metrics'] is not None) for p in data['phases']]}")
    print(f"Pilot: {len(pimgs)} images, {data['pilot']['n_published']} published, refusals {pref}")

if __name__ == '__main__':
    main()
