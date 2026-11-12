#!/usr/bin/env python3
"""Authored text traces only. No Qwen, Q4, Tiny or R2T2 inference/output generation."""
import argparse
import json
from pathlib import Path
import statistics
import time

from qwen_base_stream import PrefixCommitter, Policy, StreamError
import wer


def traces():
    target = [
        ('recover', 'a red cup opens now', ['a red cap', 'a red cup opens', 'a red cup opens now', 'a red cup opens now']),
        ('stable_wrong', 'the gate is open', ['the gate is closed', 'the gate is closed', 'the gate is open', 'the gate is open']),
        ('numbers', 'chapter three verse sixteen', ['chapter three verse', 'chapter three verse', 'chapter three verse sixteen', 'chapter three verse sixteen']),
        ('display', "God's word remains", ['God’s word', 'God’s word', "God's word remains", "God's word remains"]),
        ('repeat', 'very very clear today', ['very very', 'very very clear', 'very very clear today', 'very very clear today']),
        ('late', 'please read the line', ['', 'please read', 'please read the line', 'please read the line'])]
    rows = [{'case_id': name, 'has_target': True, 'gold': gold, 'hypotheses': hyp} for name, gold, hyp in target]
    saved = json.loads((Path(__file__).resolve().parents[1]/'data/ctrl03_saved_detection.json').read_text())
    rows.append({'case_id': 'SAVED_CTRL03_TEXT', 'has_target': False, 'gold': '',
                 'hypotheses': [saved['text']]*4, 'saved_detection_only': {'kind': 'QUOTE', 'verse_ref': 'Luke 1:17', 'confidence': .833}})
    rows += [{'case_id': f'OTHER{n:02d}', 'has_target': False, 'gold': '',
              'hypotheses': ['another voice says these words']*4} for n in range(1, 20)]
    rows += [{'case_id': f'SILENCE{n:02d}', 'has_target': False, 'gold': '', 'hypotheses': ['']*4} for n in range(1, 9)]
    return rows


def quantile(values, p):
    if not values: return None
    values = sorted(values); pos = (len(values)-1)*p
    a = int(pos); b = min(a+1, len(values)-1)
    return values[a]+(values[b]-values[a])*(pos-a)


def study():
    output = []
    for name, holdback in [('baseline_revisable_text', None), ('local_agreement_holdback_words_0', 0), ('local_agreement_holdback_words_1', 1)]:
        cases, durations, lags = [], [], []
        totals = {'ref_words': 0, 'edits': 0, 'words_on_no_target': 0, 'rejected_updates': 0,
                  'visible_prefix_rewrites': 0, 'target_cases': 6, 'other_speaker_cases': 20, 'silence_cases': 8}
        for trace in traces():
            c = PrefixCommitter(Policy(holdback)) if holdback is not None else None
            text, first_emitted, events = '', {}, []
            for index, hypothesis in enumerate(trace['hypotheses'], 1):
                at_ms = index*400
                start = time.perf_counter()
                if c is None:
                    totals['visible_prefix_rewrites'] += bool(text and not hypothesis.startswith(text))
                    text = hypothesis
                    event = {'committed_text': None, 'visible_text': text, 'rejected': False}
                else:
                    try:
                        event = c.observe(hypothesis.split(), request_id=index, audio_samples=at_ms*16, final=index == 4)
                        assert event['committed_text'].startswith(text)
                        text = event['committed_text']; event['rejected'] = False
                    except StreamError as e:
                        totals['rejected_updates'] += 1
                        event = {'committed_text': c.text, 'rejected': True, 'reason': str(e)}
                        text = c.text
                durations.append((time.perf_counter()-start)*1000)
                event['synthetic_audio_time_ms'] = at_ms
                events.append(event)
                if c is not None:
                    for word_index in range(len(wer.tokens(text))): first_emitted.setdefault(word_index, at_ms)
            gold, hyp = wer.tokens(trace['gold']), wer.tokens(text)
            edits = wer.edit_counts(gold, hyp)[3]
            if gold:
                totals['ref_words'] += len(gold); totals['edits'] += edits
                # Positional identical-word subset only; these are authored
                # timestamps (200 ms/word), not measured or forced-aligned audio.
                if c is not None:
                    for j, word in enumerate(gold):
                        if j < len(hyp) and word == hyp[j] and j in first_emitted:
                            lags.append(first_emitted[j]-200*(j+1))
            else: totals['words_on_no_target'] += len(hyp)
            cases.append({'case_id': trace['case_id'], 'has_target': trace['has_target'],
                          'gold': trace['gold'], 'final_text': text, 'hypotheses': trace['hypotheses'], 'events': events})
        totals['committed_final_wer_pct'] = 100*totals['edits']/totals['ref_words']
        output.append({'policy': name, **totals,
                       'text_wrapper_cpu_ms_p50': statistics.median(durations),
                       'text_wrapper_cpu_ms_p95': quantile(durations, .95),
                       'authored_timeline_matched_word_lag_ms_p50': quantile(lags, .5),
                       'authored_timeline_matched_word_lag_ms_p95': quantile(lags, .95),
                       'lag_matched_words': len(lags), 'actual_asr_latency_ms_p50': None,
                       'actual_asr_latency_ms_p95': None, 'asr_rtf': None, 'energy_joules': None,
                       'actual_wrong_cards': None, 'actual_correct_cards': None, 'cases': cases})
    return {'evidence_class': 'MODEL_FREE_SYNTHETIC_TEXT', 'models_executed': [],
            'source': 'new authored hypothesis fixtures plus explicitly labelled saved CTRL03 text',
            'cases_per_policy': 34, 'results': output, 'parameters_selected_on_holdout': False,
            'actual_asr_wer': None, 'card_visible': 'NOT_MEASURED', 'speaker_guard': 'UNPROVEN',
            'production': 'PRODUCTION_NO_GO'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); result = study(); args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'evidence_class': result['evidence_class'], 'models_executed': [],
                      'summary': [{k: v for k, v in r.items() if k != 'cases'} for r in result['results']]}, indent=2))
