#!/usr/bin/env python3
"""Read model headers and stream hashes; never import a model runtime or weights.

All memory figures are analytical state estimates, not measured inference RSS.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def safetensors_analysis(path):
    with Path(path).open('rb') as stream:
        size = struct.unpack('<Q', stream.read(8))[0]
        if size > 8 * 1024**2:
            raise ValueError('oversized header')
        header = json.loads(stream.read(size))
    tensors = {key: value for key, value in header.items() if key != '__metadata__'}
    dtypes = Counter(value['dtype'] for value in tensors.values())
    result = {'tensor_count': len(tensors), 'dtype_counts': dict(dtypes),
              'header_bytes': size, 'weights_loaded': False}
    if set(dtypes) == {'BF16'}:
        counts = {key: math.prod(value['shape']) for key, value in tensors.items()}
        total = sum(counts.values())
        result['stored_parameter_elements'] = total
        result['parameter_groups'] = {
            name: sum(count for key, count in counts.items() if key.startswith(prefix))
            for name, prefix in [('audio_encoder', 'thinker.audio_tower.'),
                                 ('language_decoder', 'thinker.model.')]
        }
        result['full_mixed_adam_state_bytes_estimate'] = total * 16
        lora = {}
        for rank in (8, 16):
            modules = {key: value for key, value in tensors.items()
                       if key.startswith('thinker.model.layers.') and
                       key.endswith(('.q_proj.weight', '.k_proj.weight', '.v_proj.weight', '.o_proj.weight'))}
            if any(len(value['shape']) != 2 for value in modules.values()):
                raise ValueError('LoRA target must be a matrix')
            parameters = sum(rank * sum(value['shape']) for value in modules.values())
            lora[str(rank)] = {'target_matrices': len(modules), 'trainable_parameters': parameters,
                               'mixed_adam_state_bytes_estimate': parameters * 16,
                               'activation_workspace_memory': None,
                               'feasibility': 'NOT_MEASURED_NOT_A_TRAINING_RUN'}
        result['decoder_attention_lora'] = lora
    return result


def gguf_analysis(path):
    """Bounded GGUF v3 metadata/tensor-descriptor reader, no tensor payload read."""
    with Path(path).open('rb') as stream:
        def read(size):
            if stream.tell() + size > 32 * 1024**2:
                raise ValueError('header budget exceeded')
            data = stream.read(size)
            if len(data) != size:
                raise ValueError('truncated header')
            return data

        def number(fmt):
            return struct.unpack('<' + fmt, read(struct.calcsize('<' + fmt)))[0]

        def string():
            length = number('Q')
            if length > 16 * 1024**2:
                raise ValueError('oversized metadata string')
            return read(length).decode('utf-8')

        def value(kind, depth=0):
            if depth > 2:
                raise ValueError('nested metadata')
            formats = {0: 'B', 1: 'b', 2: 'H', 3: 'h', 4: 'I', 5: 'i',
                       6: 'f', 7: '?', 10: 'Q', 11: 'q', 12: 'd'}
            if kind in formats:
                return number(formats[kind])
            if kind == 8:
                return string()
            if kind == 9:
                child, count = number('I'), number('Q')
                if count > 200000:
                    raise ValueError('oversized array')
                values = [value(child, depth + 1) for _ in range(count)]
                return {'array_count': count, 'sha256': hashlib.sha256(
                    json.dumps(values, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()}
            raise ValueError('unknown GGUF metadata type')

        if read(4) != b'GGUF' or number('I') != 3:
            raise ValueError('GGUF v3 required')
        tensor_count, metadata_count = number('Q'), number('Q')
        if tensor_count > 10000 or metadata_count > 10000:
            raise ValueError('unbounded metadata')
        metadata = {}
        for _ in range(metadata_count):
            key = string()
            metadata[key] = value(number('I'))
        types = Counter()
        tensor_names = []
        for _ in range(tensor_count):
            name = string()
            dimensions = number('I')
            if dimensions > 4:
                raise ValueError('unexpected tensor rank')
            shape = [number('Q') for _ in range(dimensions)]
            kind, _offset = number('I'), number('Q')
            types[kind] += 1
            tensor_names.append({'name': name, 'shape': shape, 'type_id': kind})
        return {'gguf_version': 3, 'tensor_count': tensor_count,
                'metadata': metadata, 'tensor_type_id_counts': dict(types),
                'tensor_descriptor_sha256': hashlib.sha256(json.dumps(tensor_names, sort_keys=True).encode()).hexdigest(),
                'header_end_bytes': stream.tell(), 'weights_loaded': False,
                'format_note': 'general.file_type is a declared mostly-format; mixed tensors remain explicit'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    result = {'path': str(args.path), 'bytes': args.path.stat().st_size, 'sha256': sha256(args.path)}
    result.update(gguf_analysis(args.path) if args.path.suffix == '.gguf' else safetensors_analysis(args.path))
    print(json.dumps(result, indent=2))
