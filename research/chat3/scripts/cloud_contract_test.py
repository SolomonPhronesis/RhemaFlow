#!/usr/bin/env python3
"""RhemaCloud manifest / checksum / redundant-restore contract test.

Synthetic ciphertext only: random bytes stand in for encrypted chunks. No keys,
no provider credentials, no network. Injected failures are simulated locally.
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 16), b''):
            h.update(block)
    return h.hexdigest()


def canonical(manifest):
    return json.dumps({k: manifest[k] for k in ('version', 'chunk_bytes', 'chunks')}, sort_keys=True)


def build(root, rng):
    for r in REPLICAS:
        (root / r).mkdir(parents=True, exist_ok=True)
    manifest = {'version': 1, 'chunk_bytes': CHUNK_BYTES, 'chunks': []}
    for i in range(CHUNKS):
        data = bytes(rng.getrandbits(8) for _ in range(CHUNK_BYTES))
        name = f'chunk_{i:03d}.bin'
        manifest['chunks'].append({'id': i, 'name': name, 'size': len(data),
                                   'sha256': hashlib.sha256(data).hexdigest()})
        for r in REPLICAS:
            (root / r / name).write_bytes(data)
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return manifest


def load_verified(root, expected_sha):
    """Read the manifest from disk and refuse if it does not match the pinned hash."""
    manifest = json.loads((root / 'manifest.json').read_text())
    if hashlib.sha256(canonical(manifest).encode()).hexdigest() != expected_sha:
        return None, 'manifest_sha256_mismatch'
    return manifest, None


def verify_chunk(path, meta):
    if not path.exists():
        return 'missing'
    if path.stat().st_size != meta['size']:
        return 'size_mismatch'
    if sha256_file(path) != meta['sha256']:
        return 'checksum_mismatch'
    return 'ok'


def restore(root, manifest, expected_sha, order=None):
    if manifest is None:
        return {'ok': False, 'error': 'manifest_sha256_mismatch', 'recovered': 0}
    if hashlib.sha256(canonical(manifest).encode()).hexdigest() != expected_sha:
        return {'ok': False, 'error': 'manifest_sha256_mismatch', 'recovered': 0}
    order = order or REPLICAS
    recovered, errors = 0, []
    for meta in manifest['chunks']:
        for r in order:
            state = verify_chunk(root / r / meta['name'], meta)
            if state == 'ok':
                recovered += 1
                break
            errors.append({'chunk': meta['id'], 'replica': r, 'state': state})
        else:
            return {'ok': False, 'error': f"chunk {meta['id']} unavailable in all replicas",
                    'recovered': recovered, 'errors': errors}
    return {'ok': True, 'recovered': recovered, 'errors': errors}


def main():
    rng = random.Random(20261111)
    root = Path(tempfile.mkdtemp(prefix='rfcloud_contract_'))
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
                                                        'chunks': manifest['chunks'][:4]}))
        tampered, err = load_verified(root, pinned)
        case('tampered_manifest_on_disk_is_rejected', restore(root, tampered, pinned), False)

        (root / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        case('restored_manifest_verifies_again', restore(root, load_verified(root, pinned)[0], pinned), True)

        truncated = root / 'eu-r2' / 'chunk_001.bin'
        truncated.write_bytes(truncated.read_bytes()[:1000])
        case('truncated_chunk_falls_back_to_peer', restore(root, manifest, pinned), True)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    Path('out').mkdir(exist_ok=True)
    Path('out/cloud_contract.json').write_text(json.dumps(results, indent=2))
    failures = [r['case'] for r in results if not r['pass']]
    for r in results:
        print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['case']}  ok={r['result']['ok']}"
              + (f"  ({r['result'].get('error')})" if not r['result']['ok'] else ''))
    print('FAILURES:', failures if failures else 'none')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
