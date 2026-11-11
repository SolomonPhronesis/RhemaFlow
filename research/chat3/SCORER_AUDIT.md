# SCORER_AUDIT — root cause, fixtures, provenance verdict

## 1. The defect (real, and shipped in the previous commit)

`research/chat3/scripts/wer.py` v1 tokenised with:

```python
re.split(r"[^a-z0-9' ]+", s)     # splits on punctuation only — spaces are inside the class
```

The negated class contains a space, so it splits on punctuation but **not on whitespace**. Result:

| input | v1 tokens | v2 tokens |
|---|---|---|
| `for god so loved the world` | `['for god so loved the world']` (1) | `['for','god','so','loved','the','world']` (6) |

Consequences measured on the saved Opus transcripts (20 clips, same audio, same transcripts):

| variant | ref words counted by v1 | ref words counted by v2 | WER v1 | WER v2 | published |
|---|---:|---:|---:|---:|---:|
| clean PCM | 89 | 487 | 13.48 % | **1.848 %** | 1.85 % |
| clean Opus 16 kbps | 89 | 487 | 13.48 % | **1.848 %** | 1.85 % |
| mixed music-0 PCM | 89 | 487 | 17.98 % | **3.285 %** | 3.29 % |
| mixed music-0 Opus 24 kbps | 89 | 487 | 19.10 % | **3.696 %** | 3.70 % |

v1 under-counted reference words by 5.5× and inflated WER by ~11–15 pp. **v1 could not even score the frozen
matrix**: matrix rows carry `fixture`, not `file`, so v1 raised `KeyError: 'file'`.

## 2. Was any published number produced by v1?

**No.** Provenance established from the artefacts, not from memory:

| Published metric set | Scorer actually used | Reproduction |
|---|---|---|
| 648-clip matrix (26.31 / 44.79 / 24.39 / 26.31) | `matrix_work/scripts/analyse_matrix.py`, tokeniser `re.sub(punct → space).split()` (correct) | re-ran on the saved raw JSONL: **exact match** (26.306 / 44.789 / 24.387 / 26.306; n=560, 15,008 ref words) |
| Opus round-trip (1.85 / 3.29 / 3.70) | ad-hoc inline scorer with the same correct `re.sub` tokeniser | re-scored with fixed v2: **exact match** (1.848 / 3.285 / 3.696) |
| Lyrics 100/95/75 % | text matcher, no WER | unchanged |
| Restore contract 9/9 | contract test, no WER | unchanged (extended to 15/15) |

**Verdict: the published metrics remain VALID; the shipped `wer.py` v1 was INVALID as a tool and is fixed in this
commit.** No published number was multiplied by the broken tokeniser.

## 3. What v2 fixes besides tokenisation

| Risk flagged in the brief | v2 behaviour |
|---|---|
| filename slicing `[:4]` could collide | explicit `case_id`, or `--manifest` mapping validated for duplicates; no inference from names |
| duplicate output rows | fail closed (`duplicate transcript for key …`) |
| missing gold rows | fail closed with exit code 2, `n_missing_gold` reported |
| empty reference vs non-empty hypothesis | excluded from WER, reported as `n_empty_ref` + `hyp_words_on_empty_ref` (false-speech volume) |
| blank reference rows in gold | allowed only if identical; conflicting text raises |
| non-JSON / truncated JSONL | fail closed with file:line |
| reordered rows | order-independent aggregation |
| one case in several conditions | `--key case_id,condition` composite identity |
| hard examples silently dropped | every row is either used, empty-ref, or an error — nothing is skipped silently |
| normalised vs verbatim | `--mode normalise|verbatim`, documented |
| provenance | output includes `n_rows`, `n_used`, `coverage_pct`, `n_ref_words`, `n_empty_ref`, S/D/I and per-condition table |

## 4. Tests

`python3 research/chat3/tests/test_wer.py -v` → **20/20 pass**, covering: phrase splitting, Unicode apostrophes,
numbers, identical/substitution/deletion/insertion, empty hypothesis, empty reference, S+D+I equals an
independent two-row DP distance on 200 random pairs, duplicate ids, missing gold, truncated JSONL, manifest
mapping, composite keys, empty-ref exclusion, conflicting gold, repeated identical gold, condition exclusion.
