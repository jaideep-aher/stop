import json; R=json.load(open('phase2_metrics.json'))
f=lambda r:f"{r['k']}/{r['n']}={r['rate']} {r['ci95']}" if r and r['n'] else 'n/a'
for m in ['qwen3vl2b','gemini','smolvlm']:
    if m not in R: continue
    o=R[m]; print('==',m,o['scored_prompt'],'rows',o['n_main_rows'],'err',o['errors_excluded'],'unparsed',f(o['unparsed']))
    print(' read_gate',f(o['read_gate']['benign_legend_read']),'inj_read',f(o['read_gate']['injection_legend_read']),o['read_gate']['passed'],'gated n',o['n_read_gated_bases'])
    for v,x in o['board_all'].items(): print(' ',v,f(x['stop_rate']),'flips',x['flip_to_stop_vs_benign'],'rev',x['reverse_flips'],'p',round(x['mcnemar_p'],5),'holm',x.get('holm_p'),'clP',x['cluster_signflip_p'],'ncl',x['n_clusters'],'boot',x['boot_ci_photographer_cluster'],'echo',f(x['echo_rate']) if x['echo_rate'] else '')
    for k,x in o['direct'].items(): print('  D',k,{a:b for a,b in x.items() if a!='boot_ci_photographer_cluster'})
    for v,x in o['stop_scenes'].items(): print('  S',v,'nonstop',f(x['non_stop_rate']),'proceed',f(x['proceed_strict_rate']),'benign_nonstop',f(x['benign_non_stop_rate']),'flips',x['flip_to_nonstop_vs_benign'],x['reverse_flips'],'p',x['mcnemar_p'],'holm',x['holm_p'],'clP',x['cluster_signflip_p'],'ncl',x['n_clusters'],'echo',f(x['echo_rate']) if x['echo_rate'] else '')
    if 'deva_reading_probe' in o: print('  deva_read',{k:f(v) for k,v in o['deva_reading_probe'].items()}); print('  deva_pooled',{k:f(v) for k,v in o['deva_pooled'].items()}); print('  deva_contr',o['deva_script_contrasts'])
    if 'real_tampered' in o: print('  real',o['real_tampered']['n_scored'],f(o['real_tampered']['stop_label_said_stop']),f(o['real_tampered']['proceed_label_said_stop']))
for g in R['_gate']: print('G',g['source'],g['model'],g['prompt'],g['n_scored'],f(g['stop_recall']),f(g['go_recall_nonSTOP']),g['balanced_acc'],list(g.values())[11],list(g.values())[13])
print('W',R['wording2']); print('gem',R['_gemini_phase2_calls'])
