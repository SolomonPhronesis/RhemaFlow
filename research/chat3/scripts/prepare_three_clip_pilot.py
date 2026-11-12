#!/usr/bin/env python3
"""Prepare an eligible clean/MP3-roundtrip/procedural-music pilot OUTSIDE Git.

Preparation only: no model or matcher execution. Pending-rights originals stay
blocked. Requires the operator's eligible provenance record and existing ffmpeg.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import wave

import numpy as np

from rf_research_audio import SCHEMA, require, validate_case


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def read_pcm(path):
    with wave.open(str(path)) as w:
        require((w.getframerate(), w.getnchannels(), w.getsampwidth()) == (16000, 1, 2), '16k mono PCM16 required')
        require(0 < w.getnframes() <= 30*16000, 'pilot source must be within the 30-second utterance budget')
        data = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float)/32768
    require(len(data) > 0 and bool(np.any(data)), 'nonempty target-speech candidate required')
    return data


def prepare(source, rights, out):
    source, out = source.resolve(), out.resolve()
    repo = Path(__file__).resolve().parents[3]
    require(not out.is_relative_to(repo), 'audio output must be outside research Git checkout')
    require(rights.get('rights_status') == 'verified' and rights.get('research_allowed') is True, 'rights/provenance blocked')
    require(rights.get('source_sha256') == sha(source), 'source provenance hash mismatch')
    require(isinstance(rights.get('gold_text'), str) and bool(rights['gold_text'].strip()), 'source target gold required')
    require(shutil.disk_usage(out.parent).free >= 8*1024**3, 'BLOCKED_DISK: require >=8 GiB before pilot preparation')
    require(shutil.which('ffmpeg') is not None, 'BLOCKED_BACKEND: ffmpeg unavailable; no install performed')
    require(not out.exists(), 'choose a fresh output directory')
    pcm = read_pcm(source)
    out.mkdir(parents=True)
    clean, encoded, decoded, music = [out/n for n in ('clean.wav', 'encoded.mp3', 'mp3_decoded.wav', 'music_0db.wav')]
    shutil.copyfile(source, clean)
    commands = [
        ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-i', str(clean), '-codec:a', 'libmp3lame', '-b:a', '128k', str(encoded)],
        ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-i', str(encoded), '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(decoded)]]
    for command in commands: subprocess.run(command, check=True, timeout=60, capture_output=True)
    require(len(read_pcm(decoded)) == len(pcm), 'roundtrip sample-count drift: do not silently trim')
    axis = np.arange(len(pcm))/16000
    bed = sum(np.sin(2*np.pi*f*axis)/3 for f in (220, 330, 440))
    bed *= np.sqrt(np.mean(pcm*pcm))/np.sqrt(np.mean(bed*bed))
    mixed = pcm+bed
    gain = min(1.0, .95/max(float(np.max(np.abs(mixed))), 1e-12))
    with wave.open(str(music), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes((mixed*gain*32767).astype('<i2').tobytes())
    cases = []
    for condition, path in [('clean', clean), ('mp3_roundtrip', decoded), ('procedural_music_0db', music)]:
        cases.append(validate_case({'schema': SCHEMA, 'case_id': 'PILOT_'+condition, 'session_id': rights.get('session_id', 'pilot'),
                       'speaker_id': rights.get('speaker_id', 'pilot-target'), 'condition': condition,
                       'cluster_id': rights['source_sha256'],
                       'evidence_class': 'SYNTHETIC_SINGLE_CHANNEL', 'split': 'holdout',
                       'rights_status': 'verified', 'research_allowed': True,
                       'channels': [{'role': 'close', 'path': path.name, 'sha256': sha(path), 'sample_rate': 16000,
                                     'samples': len(pcm), 'clock_id': 'source-file-clock'}],
                       'expected': {'has_target': True, 'gold_text': rights['gold_text'], 'verse_ref': rights.get('verse_ref', '')}}))
    (out/'cases.json').write_text(json.dumps(cases, indent=2)+'\n')
    (out/'preparation.json').write_text(json.dumps({'source_sha256': sha(source), 'encoded_mp3_sha256': sha(encoded),
                                                  'music_bed': 'independently generated three-tone instrumental surrogate; no recording',
                                                  'music_mix_gain': gain, 'music_snr_db': 0,
                                                  'ffmpeg_commands': commands, 'models_run': [], 'asr_wer': None}, indent=2)+'\n')
    return cases


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True); ap.add_argument('--rights-record', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True); args = ap.parse_args()
    print(json.dumps({'cases_prepared': len(prepare(args.source, json.loads(args.rights_record.read_text()), args.out)), 'models_run': []}))
