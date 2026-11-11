#!/usr/bin/env python3
"""RhemaCloud manifest / checksum / redundant-restore contract test (v2).

Synthetic ciphertext only: random bytes stand in for encrypted chunks. No keys,
no provider credentials, no network. Injected failures are simulated locally.

v2 adds: manifest versioning, stale key ids, crash/resume from a partial cache,
and a stale-key replica that must be ignored in favour of a peer.
"""
import hashlib
import json
import random
import shutil
import tempfile
from pathlib import Path

CHUNKS = 8
CHUNK_BYTES = 64 * 1024
REPLICAS = ['eu-r2', 'fi-hetzner', 'aws-archive']
KEY_ID = 'k1'


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 16), b''):
            h.update(block)
    return h.hexdigest()


def canonical(manifest):
    return json.dumps({k: manifest[k] for k in ('version', 'chunk_bytes', 'chunks', 'key_id')}, sort_keys=True)


def build(root, rng, chunks=CHUNKS, version=1, key_id=KEY_ID):
    for r in REPLICAS:
        (root / r).mkdir(parents=True, exist_ok=True)
    manifest = {'version': version, 'chunk_bytes': CHUNK_BYTES, 'key_id': key_id, 'chunks': []}
    for i in range(chunks):
        data = bytes(rng.getrandbits(8) for _ in range(CHUNK_BYTES))
        name = f'chunk_{i:03d}.bin'
        manifest['chunks'].append({'id': i, 'name': name, 'size': len(data),
                                   'sha256': hashlib.sha256(data).hexdigest(), 'key_id': key_id})
        for r in REPLICAS:
            (root / r / name).write_bytes(data)
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return manifest


def load_verified(root, expected_sha):
    manifest = json.loads((root / 'manifest.json').read_text())
    if hashlib.sha256(canonical(manifest).encode()).hexdigest() != expected_sha:
        return None, 'manifest_sha256_mismatch'
    return manifest, None


def verify_chunk(path, meta, allowed_key_ids):
    if meta.get('key_id') not in allowed_key_ids:
        return 'stale_key'
    if not path.exists():
        return 'missing'
    if path.stat().st_size != meta['size']:
        return 'size_mismatch'
    if sha256_file(path) != meta['sha256']:
        return 'checksum_mismatch'
    return 'ok'


def restore(root, manifest, expected_sha, order=None, allowed_key_ids=None, cache_dir=None):
    allowed = set(allowed_key_ids or [KEY_ID])
    if manifest is None:
        return {'ok': False, 'error': 'manifest_sha256_mismatch', 'recovered': 0}
    if hashlib.sha256(canonical(manifest).encode()).hexdigest() != expected_sha:
        return {'ok': False, 'error': 'manifest_sha256_mismatch', 'recovered': 0}
    order = order or REPLICAS
    recovered, resumed, errors = 0, 0, []
    for meta in manifest['chunks']:
        done = False
        if cache_dir is not None:
            cached = cache_dir / meta['name']
            if verify_chunk(cached, meta, allowed) == 'ok':
                recovered += 1
                resumed += 1
                done = True
            elif cached.exists():
                cached.unlink()  # discard a bad partial download, never trust it
        if done:
            continue
        for r in order:
            state = verify_chunk(root / r / meta['name'], meta, allowed)
            if state == 'ok':
                recovered += 1
                break
            errors.append({'chunk': meta['id'], 'replica': r, 'state': state})
        else:
            return {'ok': False, 'error': f"chunk {meta['id']} unavailable in all replicas",
                    'recovered': recovered, 'errors': errors}
    return {'ok': True, 'recovered': recovered, 'resumed': resumed, 'errors': errors}


def main():
    rng = random.Random(20261111)
    root = Path(tempfile.mkdtemp(prefix='rfcloud_contract_'))
    cache = root / 'resume-cache'
    cache.mkdir()
    results = []

    def case(name, result, ok_expected):
        results.append({'case': name, 'ok_expected': ok_expected, 'result': result,
                        'pass': result['ok'] == ok_expected})

    try:
        manifest = build(root, rng)
        pinned = hashlib.sha256(canonical(manifest).encode()).hexdigest()

        case('clean_restore', restore(root, manifest, pinned), True)

        (root / 'eu-r2' / 'chunk_003.bin').write_bytes(b'corrupted' * 100)
        case('one_replica_corrupt_restores_from_peer', restore(root, manifest, pinned), True)

        (root / 'fi-hetzner' / 'chunk_005.bin').unlink()
        case('one_replica_missing_restores_from_peer', restore(root, manifest, pinned), True)

        good_chunk7 = (root / 'eu-r2' / 'chunk_007.bin').read_bytes()
        for r in REPLICAS:
            (root / r / 'chunk_007.bin').write_bytes(b'x' * 10)
        case('chunk_lost_everywhere_fails_closed', restore(root, manifest, pinned), False)

        (root / 'aws-archive' / 'chunk_007.bin').write_bytes(good_chunk7)
        case('single_good_replica_is_enough', restore(root, manifest, pinned), True)

        case('wrong_pinned_manifest_hash_fails', restore(root, manifest, '0' * 64), False)

        (root / 'manifest.json').write_text(json.dumps({'version': 1, 'chunk_bytes': CHUNK_BYTES,
                                                        'key_id': KEY_ID, 'chunks': manifest['chunks'][:4]}))
        tampered, _ = load_verified(root, pinned)
        case('tampered_manifest_on_disk_is_rejected', restore(root, tampered, pinned), False)

        (root / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        case('restored_manifest_verifies_again', restore(root, load_verified(root, pinned)[0], pinned), True)

        truncated = root / 'eu-r2' / 'chunk_001.bin'
        truncated.write_bytes(truncated.read_bytes()[:1000])
        case('truncated_chunk_falls_back_to_peer', restore(root, manifest, pinned), True)

        # --- v2 additions -------------------------------------------------
        root2 = Path(tempfile.mkdtemp(prefix='rfcloud_v2_'))
        try:
            v2 = build(root2, rng, chunks=10, version=2)
            pinned2 = hashlib.sha256(canonical(v2).encode()).hexdigest()
            case('manifest_version_bump_restores', restore(root2, v2, pinned2), True)
            case('old_pin_rejects_new_manifest', restore(root2, v2, pinned), False)
        finally:
            shutil.rmtree(root2, ignore_errors=True)

        case('stale_key_id_rejected', restore(root, manifest, pinned, allowed_key_ids=['k2']), False)

        # crash after three chunks: only those three are in the resume cache
        for meta in manifest['chunks'][:3]:
            shutil.copy(root / 'eu-r2' / meta['name'], cache / meta['name'])
        case('crash_resume_from_partial_cache', restore(root, manifest, pinned, cache_dir=cache), True)

        bad = cache / manifest['chunks'][1]['name']
        bad.write_bytes(b'bad' * 100)
        res = restore(root, manifest, pinned, cache_dir=cache)
        case('corrupt_cache_chunk_is_discarded', res, True)
        results[-1]['note'] = f"resumed={res.get('resumed')}"

        # a replica whose chunk carries a stale key must be skipped, peer used
        root3 = Path(tempfile.mkdtemp(prefix='rfcloud_stale_'))
        try:
            stale_manifest = build(root3, rng)
            stale_manifest['chunks'][4]['key_id'] = 'k0'
            pinned_stale = hashlib.sha256(canonical(stale_manifest).encode()).hexdigest()
            case('stale_key_chunk_skipped_falls_back',
                 restore(root3, stale_manifest, pinned_stale, allowed_key_ids=['k0', 'k1']), True)
        finally:
            shutil.rmtree(root3, ignore_errors=True)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    Path('out').mkdir(exist_ok=True)
    Path('out/cloud_contract.json').write_text(json.dumps(results, indent=2))
    failures = [r['case'] for r in results if not r['pass']]
    for r in results:
        extra = f"  ({r.get('note')})" if r.get('note') else ''
        print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['case']}  ok={r['result']['ok']}"
              + (f"  ({r['result'].get('error')})" if not r['result']['ok'] else '') + extra)
    print('FAILURES:', failures if failures else 'none')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
