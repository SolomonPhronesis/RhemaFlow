# SPEAKER_PLAN — can wrong-speaker capture be reduced safely?

## 1. Evidence base (frozen matrix, measured 2026-11-10)

| Condition | Q4 WER | cards correct | cards wrong | review | none |
|---|---:|---:|---:|---:|---:|
| clean | 1.59 % | 34 | 0 | 2 | 4 |
| music −5/0/+5/+10 dB | 1.87–4.01 % | 34 each | 0 | 2 | 4 |
| chatter −5 dB | 79.57 % | 1 | 0 | 14 | 25 |
| chatter 0 dB | 26.59 % | 26 | 0 | 2 | 12 |
| competing preacher −5 dB | 93.28 % | 0 | 0 | 32 | 8 |
| competing preacher 0 dB | 68.19 % | 11 | 0 | 8 | 21 |
| mixed 0 dB | 66.88 % | 3 | 0 | 12 | 25 |
| music-only / silence | n/a | 0 | 0 | 0 | 48 |

Attribution (heuristic, machine transcripts): at −5 dB **96.4 %** of overlap errors and **90.6 %** of chatter errors
are the other speaker's words; music contributes 0 %.

## 2. Options evaluated

| Option | Status | Result |
|---|---|---|
| Mic position / channel routing | **NOT_TESTED** | corpus is single-channel; no array or dual-mic data exists |
| Target-speaker enrolment (consent) | **NOT_AVAILABLE** | no embedding model on the machine, no consented enrolment audio |
| Diarisation | **NOT_AVAILABLE** | `transcribe-cli --diarize` is moss/granite-only; Parakeet returns one segment, no speaker ids (tested) |
| Duration-aware overlap flag | **NOT_TESTED** | needs audio features this run may not generate (disk < 3 GiB) |
| Card-confidence gate 0.8 | **MEASURED — rejected** | keeps 340/365 correct cards (7 % loss), removes **0** wrong |
| Oracle abstention on overlap ≤ 0 dB | measured upper bound | loses **11** correct cards, removes **0** wrong |
| Oracle abstention on chatter ≤ 0 dB | measured upper bound | loses **27** correct cards, removes **0** wrong |
| Oracle abstention on all hard cells | measured upper bound | loses **41** correct cards, removes **0** wrong |

## 3. Conclusion — negative result, source unchanged

The current conservative gate already produces **0 wrong cards across 648 clips**; the cost of interference is
**missed cards**, not false ones. Every additional abstention policy that can be measured removes correct cards
and removes no wrong cards. Therefore **no gate is added** in this commit.

Real progress on speaker attribution requires a model that actually separates speakers (embedding/diarisation or
multi-channel capture) evaluated on consented, speaker-labelled gold — currently `BLOCKED_GOLD`.
