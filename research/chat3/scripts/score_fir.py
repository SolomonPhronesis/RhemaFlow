#!/usr/bin/env python3
import csv, json, random, sys
from collections import defaultdict
sys.path.insert(0,'/Users/solomonphronesis/Documents/deepseek-harness/default-workspace/chat3_scorer_wt/research/chat3/scripts')
import wer as W
random.seed(20261111)
BASE='/Users/solomonphronesis/Documents/deepseek-harness/default-workspace'
gold={r['case_id']:r['gold_text'] for r in csv.DictReader(open(f'{BASE}/recovery_v4_work/bench/evidence/kjv40/manifest/40_verse_gold_manifest.csv'))}
def load(p): return [json.loads(l) for l in open(p) if l.strip()]
methods=['close','room','mix','scalar','fir','fir_dt']
rows=[]; detail=[]
for m in methods:
    rs=load(f'{BASE}/rounds_restart/fir/raw/b0_{m}.jsonl')
    per=defaultdict(lambda:{'n':0,'ref':0,'edits':0,'intr':0})
    for r in rs:
        g=W.tokens(gold[r['case_id']]); h=W.tokens(r.get('text') or '')
        c=per[r['condition']]; c['n']+=1; c['ref']+=len(g); c['edits']+=W.edit_counts(g,h)[3]
        gs=set(g); c['intr']+=sum(1 for w in h if w not in gs)
    ref=sum(c['ref'] for c in per.values()); ed=sum(c['edits'] for c in per.values()); intr=sum(c['intr'] for c in per.values())
    rows.append({'method':m,'clips':sum(c['n'] for c in per.values()),'ref_words':ref,'edits':ed,
                 'wer_pct':round(100*ed/ref,3),'intrusion_per_100':round(100*intr/ref,2)})
    for cond,c in sorted(per.items()):
        detail.append({'method':m,'condition':cond,'clips':c['n'],'ref_words':c['ref'],'wer_pct':round(100*c['edits']/c['ref'],3),
                       'intrusion_per_100':round(100*c['intr']/c['ref'],2)})
with open(f'{BASE}/rounds_restart/fir/results_holdout.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
with open(f'{BASE}/rounds_restart/fir/results_holdout_detail.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(detail[0])); w.writeheader(); w.writerows(detail)
# paired bootstrap vs close
close=load(f'{BASE}/rounds_restart/fir/raw/b0_close.jsonl')
def pairs(rs):
    idx={r['case_id']+'|'+r['condition']:r for r in close}
    out=[]
    for r in rs:
        k=r['case_id']+'|'+r['condition']
        if k not in idx: continue
        g=W.tokens(gold[r['case_id']])
        out.append((len(g),W.edit_counts(g,W.tokens(idx[k].get('text') or ''))[3],W.edit_counts(g,W.tokens(r.get('text') or ''))[3]))
    return out
ci_rows=[]
for m in methods[1:]:
    pr=pairs(load(f'{BASE}/rounds_restart/fir/raw/b0_{m}.jsonl'))
    diffs=[]
    for _ in range(2000):
        s=[pr[random.randrange(len(pr))] for _ in range(len(pr))]
        ref=sum(x[0] for x in s)
        if ref: diffs.append(100*(sum(x[1] for x in s)-sum(x[2] for x in s))/ref)
    diffs.sort()
    ci_rows.append({'method':m,'delta_pp':round(rows[0]['wer_pct']-[r for r in rows if r['method']==m][0]['wer_pct'],3),
                    'ci_low':round(diffs[50],2),'ci_high':round(diffs[1949],2)})
with open(f'{BASE}/rounds_restart/fir/results_ci.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(ci_rows[0])); w.writeheader(); w.writerows(ci_rows)
for r in rows: print(r)
print('CI',ci_rows)
# cards
for f,label in [('v3_fir','fir cards'),('v3_controls','controls')]:
    rs=load(f'{BASE}/rounds_restart/fir/raw/{f}.jsonl')
    q=sum(1 for r in rs if r.get('card_kind')=='QUOTE')
    corr=sum(1 for r in rs if r.get('card_kind')=='QUOTE' and r.get('card_ref')==r.get('verse_id'))
    wrong=sum(1 for r in rs if r.get('card_kind')=='QUOTE' and r.get('card_ref')!=r.get('verse_id'))
    rev=sum(1 for r in rs if r.get('card_kind')=='REVIEW')
    none=sum(1 for r in rs if r.get('card_kind')=='NO_CARD')
    words=sum(len((r.get('text') or '').split()) for r in rs) if 'control' in label else ''
    print(label,'quote',q,'correct',corr,'wrong',wrong,'review',rev,'none',none,'words',words)
