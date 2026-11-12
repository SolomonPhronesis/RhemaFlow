#!/usr/bin/env python3
"""Score complete offline RF_RESEARCH_AUDIO_V1 cases/results, never run a model."""
import argparse
import json
from pathlib import Path

from rf_research_audio import score_paired


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cases', type=Path, required=True, help='JSON array, offline expected labels included')
    ap.add_argument('--records', type=Path, required=True, help='JSONL adapter/matcher outputs')
    ap.add_argument('--models', required=True, help='comma-separated exact model IDs')
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    cases = json.loads(args.cases.read_text())
    records = [json.loads(line) for line in args.records.read_text().splitlines() if line.strip()]
    result = score_paired(cases, records, args.models.split(','), args.baseline)
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
