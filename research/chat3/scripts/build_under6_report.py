#!/usr/bin/env python3
"""Build the offline HTML/SVG research report from frozen, classified evidence."""
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/under6_20261112'


def svg(title, subtitle, body, height=320):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" '
            f'viewBox="0 0 960 {height}" role="img" aria-label="{html.escape(title)}">'
            '<style>text{font-family:Arial,sans-serif;fill:#24334a;font-size:15px}'
            '.title{font-size:21px;font-weight:700}.note{font-size:13px;fill:#566274}</style>'
            '<rect width="100%" height="100%" fill="#f8fafc" rx="12"/>'
            f'<text x="24" y="34" class="title">{html.escape(title)}</text>'
            f'<text x="24" y="59" class="note">{html.escape(subtitle)}</text>{body}</svg>')


def figures(data):
    body = ''
    names = ['Qwen 1.7B · variant unresolved', 'Historical Parakeet Q4 arm', 'Historical Tiny.en arm']
    for n, (row, label) in enumerate(zip(data['historical'], names)):
        y = 90 + n * 58
        body += f'<text x="24" y="{y+22}">{html.escape(label)}</text>'
        body += f'<rect x="300" y="{y}" width="{row["wer_pct"]*10:.2f}" height="30" fill="#496d9a" rx="3"/>'
        body += f'<text x="{310+row["wer_pct"]*10:.2f}" y="{y+21}">{row["wer_pct"]:.3f}%</text>'
        body += f'<text x="300" y="{y+46}" class="note">{row["edits"]:,} edits / {row["reference_words"]:,} target words</text>'
    body += '<text x="24" y="295" class="note">Saved counts only · 560 target clips in 648 conditions · no new inference, no real church WER or CI.</text>'
    historic = svg('Historical synthetic WER', 'Separate from owner priority; current checkpoint equivalence is unverified.', body)
    body = ''
    for n, row in enumerate(data['models']):
        y = 82 + n * 49
        label = ['Qwen 4-bit / embed8', 'Parakeet v2 Q4', 'Parakeet v2 Q8', 'Qwen BF16'][n]
        mib = row['weight_bytes'] / 1024**2
        body += f'<text x="24" y="{y+21}">{row["owner_priority"]}. {label}</text>'
        body += f'<rect x="250" y="{y}" width="{mib/6:.2f}" height="28" fill="#64758a" rx="3"/>'
        body += f'<text x="{260+mib/6:.2f}" y="{y+21}">{mib:,.1f} MiB</text>'
    body += '<text x="24" y="306" class="note">Whole weight-file bytes measured · file size is not inference RSS, speed, accuracy or training memory.</text>'
    storage = svg('Verified weight-file size', 'Owner priority is preserved. The larger v2 Q8 is 729,574,912 bytes.', body, 330)
    values = [('ΔSIR vs close-only', .788580020352079, .7044842937966288, .8689613581455058),
              ('ΔSI-SDR vs close-only', -1.0080931410731082, -1.0683586940805554, -.9291111240354402),
              ('Target-loss stress case', -9.74342029448452, None, None)]
    def x(value): return 790 + value * 45
    body = '<line x1="790" x2="790" y1="78" y2="250" stroke="#9caabc"/>'
    for n, (name, value, low, high) in enumerate(values):
        y = 95 + n * 59
        body += f'<text x="24" y="{y+20}">{name}</text>'
        body += f'<rect x="{min(x(0),x(value)):.2f}" y="{y}" width="{abs(value)*45:.2f}" height="29" fill="{"#b0712b" if value>0 else "#b44e47"}"/>'
        if low is not None:
            body += f'<line x1="{x(low):.2f}" x2="{x(high):.2f}" y1="{y+14}" y2="{y+14}" stroke="#182536" stroke-width="3"/>'
        note = f'{value:+.3f} dB' + (f' [{low:+.3f}, {high:+.3f}]' if low is not None else ' · single stress case, no CI')
        body += f'<text x="260" y="{y+46}" class="note">{html.escape(note)}</text>'
    body += '<text x="24" y="303" class="note">Prior procedural signals · paired 95% CIs / 10 source clusters, 2,000 resamples · not speech, WER or card evidence.</text>'
    dsp = svg('Causal PBFDAF: negative safety evidence retained', 'A small interference gain did not preserve target quality; do not integrate.', body, 330)
    return historic, storage, dsp


def build():
    data = json.loads((DATA / 'report_data.json').read_text())
    tests = json.loads((DATA / 'final-tests.json').read_text()) if (DATA / 'final-tests.json').exists() else {}
    historic, storage, dsp = figures(data)
    chart_dir = ROOT / 'charts'; chart_dir.mkdir(exist_ok=True)
    for name, value in [('under6_historical_wer.svg', historic), ('under6_weight_files.svg', storage), ('under6_pbfdaf_negative.svg', dsp)]:
        (chart_dir / name).write_text(value)
    labels = ['Qwen 1.7B · 4-bit + embed8', 'Parakeet v2 · Q4_K_M', 'Parakeet v2 · Q8_0', 'Qwen 1.7B · BF16']
    rows = ''.join(f'<tr><td>{m["owner_priority"]}</td><td><strong>{label}</strong><small>{html.escape(m["precision"])} · {m["weight_bytes"]:,} bytes</small></td><td><code title="{m["weight_sha256"]}">{m["weight_sha256"][:16]}…</code></td><td>NOT RUN</td><td>Unknown</td></tr>' for m, label in zip(data['models'], labels))
    evidence = [
        ('HISTORICAL_SYNTHETIC', '648-condition matrix', '560 target clips / 15,008 words', '24.387% Qwen family; 26.306% Q4; 44.789% Tiny. Exact current checkpoint equivalence unverified.'),
        ('HISTORICAL_SYNTHETIC', 'Saved CTRL03 safety failure', '28 no-target controls / 418 ASR words', 'Wrong Luke 1:17 card at 0.833. Attribution remains unresolved.'),
        ('MODEL_FREE', 'Protocol, causality and header audit', str(tests.get('tests_run', 'Pending final')) + ' tests', 'Mechanism checks only. No model inference or church accuracy claim.'),
        ('NOT_RUN', 'Four priority inference arms', '0 new real runs', 'WER, real latency, peak RSS, power and correct-card retention remain null.'),
        ('BLOCKED', 'Real church qualification', '0 consented gold services', 'Disk, rights, matching runtime and independent gold gates prevent the pilot.')]
    with (ROOT / 'EVIDENCE_REGISTER.csv').open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n'); writer.writerow(['evidence_class','item','denominator','finding']); writer.writerows(evidence)
    erows = ''.join(f'<tr data-evidence="{kind}"><td><span class="tag">{kind}</span></td><td>{title}<small>{denom}</small></td><td>{finding}</td></tr>' for kind, title, denom, finding in evidence)
    free = data['free_bytes_at_inventory'] / 1024**3
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>RhemaFlow Chat 3 — research evidence</title>
<style>
:root{color-scheme:light;--ink:#24334a;--muted:#58677b;--line:#dbe3ed;--red:#9a3b35}*{box-sizing:border-box}body{margin:0;background:#edf2f7;color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1180px;margin:auto;padding:38px 24px 64px}a{color:#245d93;text-underline-offset:3px}header{margin-bottom:30px}.eyebrow{letter-spacing:.14em;font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase}h1{font-size:clamp(30px,5vw,48px);line-height:1.15;max-width:850px;margin:12px 0 16px}h2{font-size:24px;line-height:1.3;margin:0 0 12px}h3{font-size:18px;margin:12px 0}p{margin:10px 0}.lead{max-width:850px;color:var(--muted);font-size:18px}.alert{border-left:5px solid var(--red);background:#fff3f0;padding:18px 22px;border-radius:6px;margin:24px 0}.alert strong{color:var(--red)}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.stat,section{background:white;border:1px solid var(--line);border-radius:14px;padding:23px}.stat b{display:block;font-size:29px;line-height:1.2;margin-bottom:7px}.stat span{font-size:13px;color:var(--muted)}section{margin:22px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;min-width:720px}th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);border-bottom:2px solid var(--line);padding:12px 12px}td{vertical-align:top;border-bottom:1px solid var(--line);padding:14px 12px}small{display:block;color:var(--muted);font-size:12px;margin-top:5px}code{font-size:12px;overflow-wrap:anywhere}.tag{display:inline-block;background:#edf1f6;border:1px solid #d8e0ea;border-radius:4px;padding:3px 7px;font-size:10px;font-weight:700;letter-spacing:.02em}.chart{overflow-x:auto;margin:22px 0 10px}.chart svg{display:block;min-width:760px;max-width:100%;height:auto}.footnote{color:var(--muted);font-size:13px}.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}.two p{font-size:15px}select{font:inherit;color:var(--ink);border:1px solid #bdcad9;border-radius:6px;padding:7px 12px;background:white;margin:4px 0 16px}li{margin:7px 0}footer{border-top:2px solid var(--line);padding-top:24px;margin-top:32px;color:var(--muted);font-size:14px}.links{display:flex;flex-wrap:wrap;gap:10px 20px;margin-top:20px}@media(max-width:650px){main{padding:24px 14px 42px}.stats{grid-template-columns:1fr 1fr}.stat,section{padding:18px}.two{grid-template-columns:1fr;gap:4px}.stat b{font-size:25px}.alert{padding:16px}}@media print{body{background:white}main{padding:0}section{break-inside:avoid}.scroll,.chart{overflow:visible}.chart svg{min-width:0}select{display:none}}
</style></head><body><main><header><div class="eyebrow">RhemaFlow · Chat 3 research · 12 November 2026</div><h1>Church-speech ASR:<br>priority, evidence and safety</h1><p class="lead">A source-pinned research continuation for the M1 Pro 16 GiB. The target is real church corpus WER below 6%, with safe target-speaker cards.</p><div class="alert"><strong>PRODUCTION NO GO · accuracy target not evaluated</strong><br>No new speech inference or training was run. The known wrong-speaker card and negative filter findings remain unresolved.</div><div class="stats"><div class="stat"><b>&lt;6%</b><span>Owner goal · real WER unknown</span></div><div class="stat"><b>0</b><span>New real inference runs</span></div><div class="stat"><b>0</b><span>Consented real gold services</span></div><div class="stat"><b>__FREE__ GiB</b><span>Inventory free disk · 8 GiB pilot floor</span></div></div></header>
<section><h2>Owner’s model priority</h2><p>The order below is the requested experiment order. It is not an accuracy ranking. All checkpoints were identified and hashed without loading them.</p><div class="scroll"><table><thead><tr><th>Order</th><th>Verified local checkpoint</th><th>Weight SHA-256</th><th>New inference</th><th>Real WER</th></tr></thead><tbody>__PRIORITY__</tbody></table></div><p class="footnote">The Qwen embed8 model is mostly 4-bit with an 8-bit embedding override. The larger Parakeet v2 Q8 contains Q8/F16/F32 tensors. A separately labeled 1.256 GB v3/F16 file is not this v2 Q8. Pure-Q4 Qwen is a separately identified alternative.</p><div class="chart">__STORAGE__</div></section>
<section><h2>Evidence register</h2><label for="evidence-filter">Show evidence class</label><br><select id="evidence-filter"><option value="all">All evidence classes</option><option>HISTORICAL_SYNTHETIC</option><option>MODEL_FREE</option><option>NOT_RUN</option><option>BLOCKED</option></select><div class="scroll"><table id="evidence-table"><thead><tr><th>Class</th><th>Coverage</th><th>Finding</th></tr></thead><tbody>__EVIDENCE__</tbody></table></div><p class="footnote">NEW_REAL_INFERENCE has no rows because no such run exists. Missing measurements remain unknown, never zero error.</p></section>
<section><h2>Historical synthetic results</h2><p>These bars recompute saved edit counts. They are not a current model rerun and do not identify which current Qwen precision produced the historical transcript.</p><div class="chart">__HISTORY__</div><p class="footnote">No target line, projected improvement curve or confidence interval is drawn. Real church qualification requires independently transcribed recordings and paired cluster uncertainty.</p></section>
<section><h2>Safety failures remain visible</h2><div class="alert"><strong>CTRL03: wrong Luke 1:17 card, confidence 0.833.</strong><br>Another preacher’s quotation was accepted on target-absent chatter. Stable text, VAD, energy and a matching verse do not establish speaker ownership. Blanket card suppression would fail retention.</div><div class="chart">__DSP__</div><p class="footnote">Old scalar/FIR WER gains also retain a future-sample defect. The causal PBFDAF study is procedural audio, not an ASR benchmark; its target-loss stress case prevents a safe integration claim.</p></section>
<section><h2>Two useful research directions</h2><div class="two"><div><h3>Source-backed native inference</h3><p>NVIDIA’s official NeMo-Speech.cpp documents Apple Silicon/Metal support. Its cache-aware Nemotron English route and Sortformer diarization are candidates for an approved experiment. The inspected TDT v3 route is full-utterance only.</p><p><a href="https://github.com/NVIDIA/NeMo-Speech.cpp/blob/536b17a41bef62d2a67a40ed3df61df26a4389fe/docs/asr/models.md">Pinned runtime model capabilities</a></p></div><div><h3>Conditional weight adaptation</h3><p>The local Qwen header implies about 28.17 GB of conventional full Adam state before activations. Decoder attention LoRA would add 3.21M parameters at rank 8 or 6.42M at rank 16. Compatible training and peak memory remain unverified.</p><p>No R2T2 weights, logits, transcripts or teacher outputs are used. Bark is text-to-audio, not an ASR candidate.</p></div></div></section>
<section><h2>Smallest valid next experiment</h2><ol><li>Reach the 8 GiB pilot floor, aiming for 15 GiB for heavy work, without unapproved cleanup.</li><li>Verify consent, rights, hashes and an approved compatible local runtime.</li><li>Run the four priority models one at a time on paired clean/MP3 target clips and an independent target-absent music/chatter control.</li><li>Preserve actual transcripts, correct/wrong cards, cold/warm time, end-to-end p50/p95, RSS, energy and dropouts.</li><li>Only then expand to matched noisy-target conditions and frozen real church gold. At least three services and independent transcripts are prerequisites, not proof of accuracy.</li></ol><p>Local tests now reject evidence-class confusion, train/holdout contamination, unmatched audio, missing card observations and false retention. They do not classify a speaker or change any product.</p></section>
<section><h2>Research delivery and source boundaries</h2><p>The V1 audio exchange remains unchanged. A draft V2 proposal names the Q8 and tokenizer identities; actual Personal integration is not verified. Source exports contain no audio, weights or automatic promotion action.</p><div class="links"><a href="CHAT3_R2T2_QWEN_WEIGHTS_IDEA_MAP.md">Source idea map</a><a href="RESEARCH_PRIORITY_AND_EVIDENCE.csv">Priority CSV</a><a href="THREE_CLIP_PILOT_PLAN.md">Pilot plan</a><a href="MODEL_WEIGHT_SPACE_FEASIBILITY.md">Weight-space feasibility</a><a href="CHAT3_UNDER6_SAFETY_GATES.md">Safety gates</a><a href="CHAT3_UNDER6_RESEARCH_MANIFEST.json">Versioned manifest</a></div></section>
<footer><strong>Failure modes:</strong> wrong-speaker cards unresolved; old aligned-filter lookahead; causal target loss; rights/runtime/disk/gold gates unmet. Passing model-free tests cannot establish church WER, correct-card retention or real-time device behavior. <strong>RESEARCH_GO · PRODUCTION_NO_GO.</strong></footer></main><script>document.getElementById('evidence-filter').addEventListener('change',function(){document.querySelectorAll('[data-evidence]').forEach(row=>{row.hidden=this.value!=='all'&&row.dataset.evidence!==this.value;});});</script></body></html>'''
    for key, value in {'__FREE__': f'{free:.2f}', '__PRIORITY__': rows, '__EVIDENCE__': erows,
                       '__STORAGE__': storage, '__HISTORY__': historic, '__DSP__': dsp}.items():
        page = page.replace(key, value)
    (ROOT / 'RESEARCH_RESULTS.html').write_text(page)
    print(json.dumps({'html': 'RESEARCH_RESULTS.html', 'standalone_svgs': 3,
                      'new_real_inference': 0, 'goal_met': False}))


if __name__ == '__main__': build()
