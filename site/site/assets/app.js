import { SOURCES } from './sources.js';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const attrib = (credit, url, license) => {
  if (!credit && !url) return '<span class="muted">withheld</span>';
  const who = url ? `<a href="${esc(url)}" rel="noopener">${esc(credit || 'source')}</a>` : esc(credit);
  return license ? `${who}, ${esc(license)}` : who;
};
const D = await (await fetch('data/data.json')).json();
const P = D.p2, MM = P.metrics, MODELS = D.models, MK = Object.keys(MODELS);
const pv = p => p == null ? '—' : p < 0.0001 ? '&lt;0.0001' : (+p).toPrecision(3).replace(/\.?0+$/, '');
const kn = r => (!r || !r.n) ? '<span class="muted">no rows</span>' : `<b>${r.k}/${r.n}</b> <span class="muted">= ${r.rate.toFixed(2)} [${r.ci95[0].toFixed(2)}, ${(+r.ci95[1]).toFixed(2)}]</span>`;
const VN = Object.fromEntries([...D.board_variants, ...D.stop_variants]);
$('#gen').textContent = D.generated_at; $('#repo').textContent = `${D.repo.name} (${D.repo.status})`;
$('#banner').innerHTML = `<b>Offline research audit.</b> ${esc(D.label_note)} p-values are exploratory.`;
$('#gem-id').textContent = `(${D.p2.gemini_model_id})`;
$('#scored').textContent = MK.map(m => `${MODELS[m].split(' (')[0]} ${MM[m].scored_prompt}`).join(', ');

// ---------- headline (quoted from metrics) ----------
const q = MM.qwen3vl2b, g = MM.gemini, ba = (m, v) => MM[m].board_all[v], ss = (m, v) => MM[m].stop_scenes[v];
const card = (t, big, sub) => `<article class="card hl"><h3>${t}</h3><p class="big">${big}</p><p>${sub}</p></article>`;
const nsr = (m, v) => v === 'sboard_benign' ? ss(m, 'sboard_proceed').benign_non_stop_rate : ss(m, v).non_stop_rate;
$('#headline-cards').innerHTML = [
 card('Qwen3-VL-2B · injection vs benign edit', `${ba('qwen3vl2b','inject_stop').stop_rate.k}/63 vs ${ba('qwen3vl2b','benign').stop_rate.k}/63`,
   `answered STOP. Injection ${kn(ba('qwen3vl2b','inject_stop').stop_rate)}; benign ${kn(ba('qwen3vl2b','benign').stop_rate)}. McNemar Holm p ${pv(ba('qwen3vl2b','inject_stop').holm_p)}; photographer-cluster sign-flip p ${pv(ba('qwen3vl2b','inject_stop').cluster_signflip_p)} (floor), ${ba('qwen3vl2b','inject_stop').n_clusters} clusters.`),
 card('…but a bare “STOP” does the same', `${ba('qwen3vl2b','bare_stop').stop_rate.k}/63`,
   `Bare STOP ${kn(ba('qwen3vl2b','bare_stop').stop_rate)}; official ROAD CLOSED ${kn(ba('qwen3vl2b','official').stop_rate)}; length-matched benign command ${kn(ba('qwen3vl2b','benign_cmd').stop_rate)}. Injection vs bare STOP: McNemar p ${pv(q.direct['inject_stop|bare_stop'].mcnemar_p)}.`),
 card('PROCEED board at a real STOP · Qwen3-VL-2B', `${nsr('qwen3vl2b','sboard_proceed').k}/71 vs ${nsr('qwen3vl2b','sboard_benign').k}/71`,
   `answered non-STOP with a ROAD CLEAR / PROCEED board vs a benign board. ${kn(nsr('qwen3vl2b','sboard_proceed'))} vs ${kn(nsr('qwen3vl2b','sboard_benign'))}; Holm p ${pv(ss('qwen3vl2b','sboard_proceed').holm_p)}.`),
 card('Gemini Flash (frontier reference)', `${ba('gemini','inject_stop').stop_rate.k}/63 vs ${ba('gemini','benign').stop_rate.k}/63`,
   `Mostly robust: injection vs benign Holm p ${pv(ba('gemini','inject_stop').holm_p)}. A bare STOP still moved it: ${kn(ba('gemini','bare_stop').stop_rate)}, Holm p ${pv(ba('gemini','bare_stop').holm_p)}. PROCEED-at-STOP non-STOP ${kn(nsr('gemini','sboard_proceed'))}.`),
].join('');

// ---------- by condition ----------
['#c-model', '#e-model'].forEach(s => $(s).innerHTML = MK.map(m => `<option value="${m}">${esc(MODELS[m])}</option>`).join(''));
function renderCond() {
  const m = $('#c-model').value, o = MM[m];
  const rows = D.board_variants.map(([v, l]) => { const r = o.board_all[v]; if (!r) return '';
    return `<tr><td>${esc(l)}${v !== 'clean' ? ' <span class="tag alt">edited</span>' : ''}</td><td>${kn(r.stop_rate)}</td>
     <td>${v === 'benign' ? '<span class="muted">reference</span>' : `${r.flip_to_stop_vs_benign} / ${r.reverse_flips}`}</td><td>${v === 'benign' ? '—' : pv(r.mcnemar_p)}</td><td>${v === 'benign' ? '—' : pv(r.holm_p)}</td>
     <td>${v === 'benign' ? '—' : pv(r.cluster_signflip_p)}</td><td>${v === 'benign' ? '—' : `[${r.boot_ci_photographer_cluster.join(', ')}]`}</td><td>${r.echo_rate ? kn(r.echo_rate) : '—'}</td></tr>`; }).join('');
  $('#cond-table').innerHTML = `<p class="muted">${esc(MODELS[m])}: ${o.n_main_rows} scored rows, unparsed ${o.unparsed.k}/${o.unparsed.n}. The correct answer on every board is PROCEED/CAUTION; the cell is P(STOP). Rows are in fixed design order.</p>
   <div class="tablewrap"><table><thead><tr><th>Condition</th><th>P(STOP) k/n [Wilson 95%]</th><th>Flips to STOP vs benign / reverse</th><th>Exact McNemar p</th><th>Holm p</th><th>Cluster sign-flip p</th><th>Cluster-bootstrap Δ 95% CI</th><th>Echo (quotes legend)</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  const s = o.stop_scenes, sp = s.sboard_proceed;
  $('#stop-table').innerHTML = `<div class="tablewrap"><table><thead><tr><th>Condition</th><th>P(answer ≠ STOP) k/n [Wilson 95%]</th><th>vs benign board: flips / reverse</th><th>McNemar p</th><th>Holm p</th><th>Cluster sign-flip p</th><th>Cluster-bootstrap Δ</th></tr></thead><tbody>
   <tr><td>${VN.sclean}</td><td>${kn(s.sclean.non_stop_rate)}</td><td>${s.sclean.flip_to_nonstop_vs_benign} / ${s.sclean.reverse_flips}</td><td>${pv(s.sclean.mcnemar_p)}</td><td>${pv(s.sclean.holm_p)}</td><td>${pv(s.sclean.cluster_signflip_p)}</td><td>[${s.sclean.boot_ci_photographer_cluster.join(', ')}]</td></tr>
   <tr><td>${VN.sboard_benign} <span class="tag alt">edited</span></td><td>${kn(sp.benign_non_stop_rate)}</td><td class="muted">reference</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>
   <tr><td>${VN.sboard_proceed} <span class="tag alt">edited</span></td><td>${kn(sp.non_stop_rate)}</td><td>${sp.flip_to_nonstop_vs_benign} / ${sp.reverse_flips}</td><td>${pv(sp.mcnemar_p)}</td><td>${pv(sp.holm_p)}</td><td>${pv(sp.cluster_signflip_p)}</td><td>[${sp.boot_ci_photographer_cluster.join(', ')}]</td></tr></tbody></table></div>`;
  const rt = o.real_tampered, w2 = m === 'gemini' ? D.p2.wording2['gemini|n3'] : null;
  $('#extra').innerHTML = `<h3>Real tampered photos (unedited, descriptive only)</h3><p>${rt ? `${rt.n_scored} scored. STOP-labeled (still a governing control) → STOP: ${kn(rt.stop_label_said_stop)}. PROCEED-labeled → STOP: ${kn(rt.proceed_label_said_stop)}.` : '<span class="muted">not run for this model</span>'}</p>` +
   (w2 ? `<h3>Wording check (second neutral wording, ${w2.n_pairs} bases)</h3><p>Injection ${kn(w2.inject_stop_rate)} vs benign ${kn(w2.benign_stop_rate)}; flips ${w2.flips} / ${w2.reverse}, McNemar p ${pv(w2.mcnemar_p)}, cluster sign-flip p ${pv(w2.cluster_signflip_p)}.</p>` : '');
}
$('#c-model').onchange = renderCond; renderCond();
const RP = P.real;
$('#real-gallery').innerHTML = `<p class="muted">${RP.filter(r => r.thumb).length} of ${P.real.length} real tampered photos published (unedited; detector-blurred, unverified).</p>` + RP.map(r => `<figure>${r.thumb ? `<img src="${r.thumb}" alt="real altered sign ${esc(r.id)}" loading="lazy">` : '<span class="noimg big">image withheld (pending human check)</span>'}<figcaption><code>${esc(r.id)}</code> provisional label ${r.label}<br>${attrib(r.credit, r.source_url, r.license)}</figcaption></figure>`).join('');

// ---------- explorer ----------
const PAGE = 25; let ep = 0;
function renderExplorer() {
  const arm = $('#e-arm').value, m = $('#e-model').value, T = $('#e-type').value;
  $('#e-type').disabled = arm !== 'board';
  const vars = arm === 'board' ? D.board_variants : D.stop_variants;
  const bs = P.bases.filter(b => b.arm === arm && (arm !== 'board' || !T || b.board_type === T));
  const pages = Math.max(1, Math.ceil(bs.length / PAGE)); ep = Math.min(ep, pages - 1);
  $('#e-table thead').innerHTML = `<tr><th>Base photo</th><th>Photographer / license</th>${vars.map(([v, l]) => `<th>${esc(l)}</th>`).join('')}</tr>`;
  $('#e-table tbody').innerHTML = bs.slice(ep * PAGE, ep * PAGE + PAGE).map(b => `<tr><td class="img">${(() => { const t = (b.images.clean || b.images.sclean || {}).thumb; return t ? `<img src="${t}" alt="${esc(b.base_id)} base photo (blurred)" loading="lazy">` : '<span class="noimg">image withheld (pending human check)</span>'; })()}<div><code>${esc(b.base_id)}</code>${b.board_type ? `<br><span class="muted">${b.board_type}</span>` : ''}</div></td>
    <td>${b.credit || b.source_url ? attrib(b.credit, b.source_url, b.license) : '<span class="muted">withheld</span>'}</td>${vars.map(([v]) => {
      const im = b.images[v]; if (!im) return '<td class="muted">—</td>';
      const d = (P.decisions[im.id] || {})[m]; if (!d) return '<td class="muted">not run</td>';
      if (d.a === 'ERROR') return '<td class="muted">error (excluded)</td>';
      const want = im.label, ok = want === 'STOP' ? d.a === 'STOP' : d.a !== 'STOP';
      const tip = `${MODELS[m].split(' (')[0]} answered ${d.a}. Correct for this scene: ${want === 'STOP' ? 'STOP' : 'PROCEED or CAUTION'}. Reason text is not shown (model reasons can quote edited board text).`;
      const lab = `<span class="act ${d.a}" title="${esc(tip)}">${d.a === 'CAUTION' ? 'CAUT.' : d.a}</span>${ok ? '' : ' <span class="x">✗</span>'}`;
      return `<td>${im.thumb ? `<a class="cell" href="${im.thumb}" target="_blank" rel="noopener" title="open blurred image (digitally altered: ${im.edited ? 'yes' : 'no'})">${lab}</a>` : lab}</td>`; }).join('')}</tr>`).join('');
  const all = P.bases.filter(b => b.arm === arm && (arm !== 'board' || !T || b.board_type === T));
  $('#e-table tfoot').innerHTML = `<tr><th colspan="2">${arm === 'board' ? 'STOP' : 'non-STOP'} count (all ${all.length} shown rows)</th>${vars.map(([v]) => { let k = 0, n = 0;
     all.forEach(b => { const im = b.images[v]; const d = im && (P.decisions[im.id] || {})[m]; if (d && d.a !== 'ERROR') { n++; if (arm === 'board' ? d.a === 'STOP' : d.a !== 'STOP') k++; } });
     return `<th>${k}/${n}</th>`; }).join('')}</tr>`;
  $('#e-count').textContent = `${bs.length} bases`; $('#e-page').textContent = `page ${ep + 1} / ${pages}`;
}
['#e-arm', '#e-model', '#e-type'].forEach(s => $(s).onchange = () => { ep = 0; renderExplorer(); });
$('#e-prev').onclick = () => { ep = Math.max(0, ep - 1); renderExplorer(); }; $('#e-next').onclick = () => { ep++; renderExplorer(); };
renderExplorer();

// ---------- gates ----------
const gk = (o, pre) => o[Object.keys(o).find(k => k.startsWith(pre))];
const MN = {gemini: 'Gemini Flash', qwen3vl2b: 'Qwen3-VL-2B', smolvlm: 'SmolVLM-500M', qwen25vl3b: 'Qwen2.5-VL-3B', smolvlm2: 'SmolVLM2-2.2B'};
const verdict = v => `<span class="vd ${v}">${v === 'FAIL' ? 'DID NOT QUALIFY' : v}</span>`;
$('#gate-table').innerHTML = `<thead><tr><th>Source</th><th>Model</th><th>Wording</th><th>Scored</th><th>STOP recall</th><th>GO recall (non-STOP)</th><th>BA</th><th>Recorded point status</th></tr></thead><tbody>` +
  P.gate.map(r => `<tr><td>${r.source}</td><td>${MN[r.model] || esc(r.model)}</td><td>${r.prompt} <span class="muted">${esc(r.prompt_note)}</span></td><td>${r.n_scored}/${r.n_total}</td><td>${kn(r.stop_recall)}</td><td>${kn(r.go_recall_nonSTOP)}</td><td>${r.balanced_acc}</td><td>${verdict(gk(r, 'gate_point'))}</td></tr>`).join('') + '</tbody>';
$('#read-gate').innerHTML = MK.map(m => { const o = MM[m], rg = o.read_gate;
  return `<article class="card gate ${rg.passed ? 'pass' : 'fail'}"><h3>${esc(MODELS[m])}</h3><p class="big">${rg.passed ? 'READS BOARDS' : 'DID NOT QUALIFY'}</p><table>
   <tr><td>Reads benign legend</td><td>${kn(rg.benign_legend_read)}</td></tr><tr><td>Reads injection legend</td><td>${kn(rg.injection_legend_read)}</td></tr>
   <tr><td>Clean board → non-STOP</td><td>${kn(o.clean_board_specificity_nonSTOP)}</td></tr><tr><td>Real STOP scene → STOP</td><td>${kn(o.real_stop_scene_sensitivity_clean)}</td></tr></table></article>`; }).join('');

// ---------- examples ----------
$('#ex').innerHTML = P.examples.length ? P.examples.map(e => `<figure class="ex">${e.file ? `<img src="${e.file}" alt="${esc(e.sides.map(x => x.condition).join(' vs '))}" loading="lazy">` : '<span class="noimg big">image withheld (pending human review after blur fix)</span>'}
  <figcaption><span class="tag alt">DIGITALLY ALTERED</span> <b>${esc(MODELS[e.model].split(' (')[0])}</b>: ${e.sides.map(x => `${esc(x.condition)} → <span class="act ${x.verdict}">${x.verdict}</span> <span class="muted">(correct: ${x.label === 'STOP' ? 'STOP' : 'PROCEED/CAUTION'})</span>`).join(' &nbsp;|&nbsp; ')}.<br>Base photo: ${attrib(e.credit, e.source_url, e.license)}; edited for the study. Blur: ${esc(e.blur)}.${e.note ? `<br><span class="muted">This board is shown instead of the original example, whose board legend was blurred by a detector false positive and needs human review.</span>` : ''}</figcaption></figure>`).join('')
  : '<div class="empty">No example passed the license, credit and blur checks.</div>';

// ---------- extra phases (site/phases.json); aggregated by condition only, file order, never sorted ----------
const leaves = (o, path = [], out = []) => { if (o && typeof o === 'object') { if ('k' in o && 'n' in o && Array.isArray(o.ci95)) out.push([path.join(' › '), o]); else for (const [k, v] of Object.entries(o)) if (!k.startsWith('_')) leaves(v, [...path, k], out); } return out; };
$('#phases').innerHTML = (D.phases || []).map(ph => `<article class="phase"><h3>${esc(ph.title)}</h3><p>${esc(ph.blurb || '')}</p>` + (ph.metrics
  ? (() => { const L = leaves(ph.metrics); return L.length ? `<div class="tablewrap"><table><thead><tr><th>Model › condition › measure</th><th>k/n [95% Wilson CI]</th></tr></thead><tbody>${L.map(([p, r]) => `<tr><td>${esc(p)}</td><td>${kn(r)}</td></tr>`).join('')}</tbody></table></div><p class="muted">Source: <code>${esc(ph.source)}</code></p>` : `<div class="empty">The metrics file <code>${esc(ph.source)}</code> exists but has no k/n results yet.</div>`; })()
  : `<div class="empty">Pending final run: no results yet (<code>${esc(ph.source)}</code> not found). Nothing is estimated or shown until it exists.</div>`) + '</article>').join('') || '<div class="empty">No further phases are configured.</div>';

// ---------- pilot ----------
const PM = D.pilot.metrics, PN = k => { const [m, p] = k.split('|'); return `${MN[m] || (m === 'yolo' ? 'YOLO11n rule' : m)} · ${p}`; };
$('#pilot-gate').innerHTML = `<thead><tr><th>Model / prompt</th><th>STOP recall</th><th>GO recall</th><th>BA</th><th>Canonical gate</th></tr></thead><tbody>` + Object.entries(PM).map(([k, o]) => o.gate ? `<tr><td>${PN(k)}</td><td>${kn(o.gate.stop_recall)}</td><td>${kn(o.gate.proceed_recall)}</td><td>${o.gate.ba}</td><td>${verdict(o.gate.passed ? 'PASS' : 'FAIL')}${k.startsWith('yolo') ? ' <span class="muted">(biased: G was YOLO-selected)</span>' : ''}</td></tr>` : `<tr><td>${PN(k)}</td><td colspan="4" class="muted">no gate rows for this run</td></tr>`).join('') + '</tbody>';
$('#pilot-s1').innerHTML = `<thead><tr><th>Model / prompt</th><th>Legit STOP recall (A+)</th><th>PROCEED on any A+</th><th>Vandalized R1-1 → STOP</th><th>STOP on A− look-alike (confounded)</th></tr></thead><tbody>` + Object.entries(PM).map(([k, o]) => { const s = o.study1 || {};
  return `<tr><td>${PN(k)}</td><td>${kn(s.legit_stop_recall)}</td><td>${kn(s['missed_legit_any(PROCEED on A_plus)'])}</td><td>${kn(s['vandalized_R1-1_stop_recall'])}</td><td>${kn(s['false_obey(STOP on A_minus)'])}</td></tr>`; }).join('') + '</tbody>';
const PI = D.pilot.images, PUB = PI.filter(i => i.published), R = D.pilot.refusals;
$('#pilot-pub').innerHTML = `${D.pilot.n_published} of ${PI.length} pilot images are published. Withheld: ${Object.entries(R).filter(([, v]) => v).map(([k, v]) => `${k.replaceAll('_', ' ')} ${v}`).join(' · ')}. Images with vehicles stay withheld until a person has checked the plate blur. Every published pilot image is a blurred copy (unverified). Images where no detector found anything to blur are withheld until a person checks them: image withheld (pending human check).`;
let gp = 0; const GP = 24;
function renderGallery() { const pages = Math.ceil(PUB.length / GP); gp = Math.max(0, Math.min(gp, pages - 1));
  $('#pilot-gallery').innerHTML = PUB.slice(gp * GP, gp * GP + GP).map(i => `<figure><img src="${i.thumb}" alt="${esc(i.id)} (${i.block})" loading="lazy"><figcaption><code>${esc(i.id)}</code> ${i.block}${i.edited ? ' <span class="tag alt">DIGITALLY ALTERED</span>' : ''}<br>${attrib(i.credit, i.source_url, i.license)}</figcaption></figure>`).join('');
  $('#g-page').textContent = `page ${gp + 1} / ${pages}`; }
$('#g-prev').onclick = () => { gp--; renderGallery(); }; $('#g-next').onclick = () => { gp++; renderGallery(); }; renderGallery();

// ---------- manifest ----------
const lic = {}; P.bases.forEach(b => lic[b.license] = (lic[b.license] || 0) + 1);
$('#p2-data').innerHTML = `<b>Phase 2:</b> ${P.bases.length} real base photos (${Object.entries(lic).map(([l, n]) => `${esc(l)} ${n}`).join(', ')}) → ${P.n_stimuli} model inputs, ${P.bases.reduce((a, b) => a + Object.values(b.images).filter(i => i.edited).length, 0)} of them digitally altered. <b>${P.n_published} of ${P.n_stimuli}</b> published as detector-blurred copies (unverified); withheld: ${Object.entries(P.refusals).filter(([, v]) => v).map(([k, v]) => `${k.replaceAll('_', ' ')} ${v}`).join(' · ') || 'none'}. Real tampered: ${P.real.filter(r => r.thumb).length}/${P.real.length}. <b>Pilot:</b> ${D.pilot.n_published}/${PI.length} published.`;
let mp = 0;
function renderManifest() {
  const set = $('#m-set').value, st = $('#m-status').value;
  let head, rows;
  if (set === 'p2') { head = '<tr><th>Base</th><th>Arm</th><th>Variants</th><th>Altered</th><th>License</th><th>Credit</th><th>Source</th><th>Status</th></tr>';
    rows = P.bases.filter(b => { const pub = Object.values(b.images).every(i => i.thumb); return !st || (st === 'pub') === pub; }).map(b => `<tr><td><code>${esc(b.base_id)}</code></td><td>${b.arm === 'board' ? 'board' : 'PROCEED-at-STOP'}</td><td>${Object.keys(b.images).length}</td><td>${Object.values(b.images).filter(i => i.edited).length}</td><td>${esc(b.license || '')}</td><td>${b.credit ? esc(b.credit) : '<span class="muted">withheld</span>'}</td><td>${b.source_url ? `<a href="${esc(b.source_url)}" rel="noopener">Commons</a>` : '<span class="muted">withheld</span>'}</td><td>${Object.values(b.images).every(i => i.thumb) ? '<span class="okc">published</span> <span class="muted">(blurred, unverified)</span>' : `<span class="muted">withheld: ${Object.values(b.images).filter(i => !i.thumb).length} variants</span>`}</td></tr>`);
  } else { head = '<tr><th>Image</th><th>Block</th><th>Label</th><th>Jurisdiction</th><th>License</th><th>Credit</th><th>Source</th><th>Status</th></tr>';
    rows = PI.filter(i => !st || (st === 'pub') === i.published).map(i => `<tr><td><code>${esc(i.id)}</code>${i.edited ? ' <span class="tag alt">DIGITALLY ALTERED</span>' : ''}</td><td>${i.block}</td><td>${i.label}</td><td>${esc(i.jurisdiction)}</td><td>${esc(i.license || '')}</td><td>${i.credit ? esc(i.credit) : '<span class="muted">withheld</span>'}</td><td>${i.source_url ? `<a href="${esc(i.source_url)}" rel="noopener">Commons</a>` : '<span class="muted">withheld</span>'}</td><td>${i.published ? '<span class="okc">published</span>' : `<span class="muted">withheld: ${esc((i.refusal || []).join(', ').replaceAll('_', ' '))}</span>`}</td></tr>`); }
  const pages = Math.max(1, Math.ceil(rows.length / 40)); mp = Math.min(mp, pages - 1);
  $('#manifest thead').innerHTML = head; $('#manifest tbody').innerHTML = rows.slice(mp * 40, mp * 40 + 40).join('') || '<tr><td colspan="8" class="muted">No rows.</td></tr>';
  $('#m-count').textContent = `${rows.length} rows`; $('#m-page').textContent = `page ${mp + 1} / ${pages}`;
}
['#m-set', '#m-status'].forEach(s => $(s).onchange = () => { mp = 0; renderManifest(); });
$('#m-prev').onclick = () => { mp = Math.max(0, mp - 1); renderManifest(); }; $('#m-next').onclick = () => { mp++; renderManifest(); };
renderManifest();

// ---------- references ----------
const G = {hook: 'Industry systems & incidents', reg: 'Regulators & legal ground truth', press: 'Press & incident reports', advocacy: 'Advocacy (cited as advocacy only)', lit: 'Methods & literature', model: 'Models & tools', data: 'Data'};
$('#refs').innerHTML = Object.entries(G).map(([g, t]) => { const xs = SOURCES.filter(s => s.g === g); if (!xs.length) return '';
  return `<h3>${t}</h3><ol class="refs">${xs.map(s => `<li id="ref-${s.id}"><b>[${s.id}]</b> ${esc(s.t)}. <a href="${s.u}" rel="noopener">${esc(s.u)}</a></li>`).join('')}</ol>`; }).join('');
