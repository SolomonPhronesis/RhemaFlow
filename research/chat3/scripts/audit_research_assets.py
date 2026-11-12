#!/usr/bin/env python3
"""Local read-only metadata/hash audit. No extraction, model loading or uploads."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import wave
import zipfile

import wer

BASE = Path('/Users/solomonphronesis/Documents/deepseek-harness/default-workspace')
DOWNLOADS = Path('/Users/solomonphronesis/Downloads')
EVIDENCE_ZIPS = ('Real_Speaker_Validation', 'Adaptive_FIR_Isolation', 'Causal_DualMic_Validation',
                 'PostRestart_Isolation', 'R2T2_Streaming_Research', 'Scorer_Speaker_Lyrics', 'Speaker_Isolation_Plan')


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def probe(path, hash_file=False):
    row = {'path': str(path)}
    try:
        if path.is_dir():
            list(path.iterdir())
        else:
            with path.open('rb') as f: f.read(1)
        row.update(status='FOUND_AND_READABLE', is_symlink=path.is_symlink(),
                   resolved_path=str(path.resolve()), bytes=path.stat().st_size if path.is_file() else None)
        if hash_file and path.is_file(): row['sha256'] = sha256(path)
    except PermissionError:
        row.update(status='EXISTS_DENIED', detail='Probe denied; a denied ancestor does not prove the leaf exists.')
    except FileNotFoundError:
        row['status'] = 'NOT_FOUND'
    except OSError as e:
        row.update(status='NOT_FOUND', detail=type(e).__name__)
    return row


def audit():
    paths = [BASE/'recovery_v4_work/bench/evidence/kjv40/manifest/40_verse_gold_manifest.csv',
             BASE/'recovery_v4_work/bench/sources/music_freely_16k.wav',
             BASE/'recovery_v4_work/bench/sources/chatter_pewbeam_16k.wav',
             BASE/'recovery_v4_work/bench/sources/overlap_smartverse_16k.wav',
             BASE/'RF_CHAT3_NEXT_20261110/external/qwen_mlx_adapter.sh',
             BASE/'rounds_restart/fir', DOWNLOADS/'RhemaFlow_Personal_Chat3_Qwen_R2T2_Codex_20261112.zip']
    paths += [root/f'RhemaFlow_Chat3_{name}_20261111.zip' for root in (BASE, DOWNLOADS) for name in EVIDENCE_ZIPS]
    path_rows = [probe(p) for p in paths]
    archives, recovered = [], []
    packages = sorted(p for p in DOWNLOADS.glob('*.zip') if 'CHAT3' in p.name.upper() and 'TANKSAGE' not in p.name.upper())
    for path in packages:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            unsafe = any(Path(n).is_absolute() or '..' in Path(n).parts for n in names)
            archive = {'path': str(path), 'status': 'FOUND_AND_READABLE', 'entries': len(names),
                       'unsafe_paths': unsafe, 'audio_entries': [n for n in names if Path(n).suffix.lower() in ('.wav', '.mp3', '.npy', '.npz')]}
            archives.append(archive)
            if unsafe: continue
            for entry in names:
                if not entry.endswith('40_KJV_WAV_GOLD.zip'): continue
                meta = z.getinfo(entry)
                if meta.file_size > 32*1024*1024: raise ValueError('metadata audit nested ZIP size budget exceeded')
                data = z.read(entry)
                with zipfile.ZipFile(io.BytesIO(data)) as nested:
                    if any(Path(n).is_absolute() or '..' in Path(n).parts for n in nested.namelist()):
                        raise ValueError('unsafe nested ZIP path')
                    gold = nested.read('manifest/40_verse_gold_manifest.csv')
                    rows = list(csv.DictReader(io.StringIO(gold.decode())))
                    clips = []
                    for r in rows:
                        if nested.getinfo(r['wav_path']).file_size > 4*1024*1024: raise ValueError('oversized WAV audit')
                        audio = nested.read(r['wav_path'])
                        actual = hashlib.sha256(audio).hexdigest()
                        with wave.open(io.BytesIO(audio)) as w:
                            clips.append({'case_id': r['case_id'], 'sha256': actual,
                                          'hash_matches': actual == r['sha256'], 'sample_rate': w.getframerate(),
                                          'channels': w.getnchannels(), 'sample_width': w.getsampwidth(),
                                          'frames': w.getnframes(), 'rights_status': r['rights_status']})
                    recovered.append({'archive': str(path), 'entry': entry, 'status': 'FOUND_AND_READABLE',
                                      'nested_zip_sha256': hashlib.sha256(data).hexdigest(),
                                      'gold_manifest_sha256': hashlib.sha256(gold).hexdigest(),
                                      'cases': len(rows), 'unique_case_ids': len({r['case_id'] for r in rows}),
                                      'word_count_whitespace': sum(len(r['gold_text'].split()) for r in rows),
                                      'word_count_existing_wer_normalizer': sum(len(wer.tokens(r['gold_text'])) for r in rows),
                                      'rights_statuses': sorted({r['rights_status'] for r in rows}),
                                      'redistribution_status': 'RIGHTS_PENDING_DO_NOT_UPLOAD',
                                      'asr_run': 'NOT_RUN_DISK_GATE_AND_RIGHTS_PENDING', 'clips': clips})
    models = []
    for root in [Path('/Users/solomonphronesis/Prosperous Projects/RF-H/out'),
                 Path('/Users/solomonphronesis/Prosperous Projects/RF-Personal-0936/v2models'),
                 Path('/Users/solomonphronesis/.rhemaflow-models')]:
        row = probe(root)
        if row['status'] == 'FOUND_AND_READABLE':
            matches = [p for p in root.iterdir() if 'qwen' in p.name.lower() or 'Q4_K_M' in p.name or 'tiny.en' in p.name]
            row['matching_entries'] = [probe(p, hash_file=p.is_file()) for p in matches]
        models.append(row)
    qwen_models = []
    model_root = Path('/Users/solomonphronesis/Prosperous Projects/RF-H/out/RF-EN-REDUCTION-PILOT/models')
    try:
        candidates = sorted(model_root.glob('qwen3-asr-1.7b*'))
        for p in candidates:
            config_path = p/'config.json'
            config = json.loads(config_path.read_text())
            weights = []
            for weight in sorted(p.glob('*.safetensors')):
                with weight.open('rb') as f:
                    size = struct.unpack('<Q', f.read(8))[0]
                    if size > 8*1024*1024: raise ValueError('oversized safetensors header')
                    header = json.loads(f.read(size))
                dtypes = {}
                for key, value in header.items():
                    if key != '__metadata__': dtypes[value['dtype']] = dtypes.get(value['dtype'], 0)+1
                weights.append(dict(probe(weight, hash_file=True), tensor_dtypes=dtypes))
            prune = p/'RF_PRUNE_MANIFEST.json'
            prune_data = json.loads(prune.read_text()) if prune.is_file() else {}
            qwen_models.append({'path': str(p), 'is_symlink': p.is_symlink(), 'resolved_path': str(p.resolve()),
                                'status': 'FOUND_AND_READABLE', 'model_type': config.get('model_type'),
                                'architectures': config.get('architectures'), 'quantization': config.get('quantization'),
                                'config_sha256': sha256(config_path), 'weights': weights,
                                'prune_manifest_sha256': sha256(prune) if prune.is_file() else None,
                                'prune_manifest_keys': sorted(prune_data),
                                'local_license_file': (p/'LICENSE').is_file(),
                                'inference': 'NOT_RUN', 'format': 'safetensors; mixed packed tensors for quantized variants'})
    except OSError as e:
        qwen_models.append({'path': str(model_root), 'status': 'EXISTS_DENIED' if isinstance(e,PermissionError) else 'NOT_FOUND'})
    free = shutil.disk_usage('.').free
    return {'paths': path_rows, 'archives': archives, 'recovered_kjv': recovered,
            'model_probes': models, 'free_bytes': free, 'asr_min_free_bytes': 8*1024**3,
            'asr_disk_gate_pass': free >= 8*1024**3, 'qwen_model_precision_and_hash': qwen_models,
            'qwen_b_product_loop': 'NOT_TESTED_NO_PRODUCT_LAUNCH',
            'swap': subprocess.check_output(['sysctl','vm.swapusage'],text=True).strip(),
            'physical_ram_bytes': int(subprocess.check_output(['sysctl','-n','hw.memsize'],text=True)),
            'no_audio_extracted_or_uploaded': True, 'no_model_loaded_or_downloaded': True}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); result = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'recovered_kjv_archives': len(result['recovered_kjv']),
                      'recovered_kjv_unique_audio_sets': len({r['nested_zip_sha256'] for r in result['recovered_kjv']}),
                      'free_gib': result['free_bytes']/1024**3,
                      'asr_disk_gate_pass': result['asr_disk_gate_pass'],
                      'qwen': result['qwen_model_precision_and_hash']}, indent=2))
