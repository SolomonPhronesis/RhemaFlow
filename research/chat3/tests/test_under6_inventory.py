import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from under6_model_inventory import gguf_analysis, safetensors_analysis


def string(text):
    raw = text.encode()
    return struct.pack('<Q', len(raw)) + raw


class InventoryTests(unittest.TestCase):
    def test_gguf_descriptor_stops_before_payload(self):
        header = b'GGUF' + struct.pack('<IQQ', 3, 1, 2)
        header += string('general.name') + struct.pack('<I', 8) + string('authored toy')
        header += string('general.file_type') + struct.pack('<II', 4, 7)
        header += string('matrix') + struct.pack('<IQQIQ', 2, 32, 64, 8, 0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'toy.gguf'; path.write_bytes(header + b'not-a-real-weight' * 100)
            result = gguf_analysis(path)
            self.assertEqual(result['header_end_bytes'], len(header))
            self.assertEqual(result['tensor_type_id_counts'], {8: 1})
            self.assertFalse(result['weights_loaded'])

    def test_truncated_or_wrong_gguf_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'toy.gguf'
            for data in (b'bad!', b'GGUF' + struct.pack('<IQQ', 3, 1, 2)):
                path.write_bytes(data)
                with self.assertRaises((ValueError, struct.error)): gguf_analysis(path)

    def test_bf16_analytic_state_is_not_runtime_measurement(self):
        tensors = {'thinker.model.layers.0.self_attn.q_proj.weight':
                   {'dtype': 'BF16', 'shape': [64, 32], 'data_offsets': [0, 4096]}}
        raw = json.dumps(tensors).encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'toy.safetensors'
            path.write_bytes(struct.pack('<Q', len(raw)) + raw)
            result = safetensors_analysis(path)
            self.assertEqual(result['stored_parameter_elements'], 2048)
            self.assertEqual(result['full_mixed_adam_state_bytes_estimate'], 32768)
            self.assertEqual(result['decoder_attention_lora']['8']['trainable_parameters'], 768)
            self.assertIsNone(result['decoder_attention_lora']['8']['activation_workspace_memory'])

    def test_packed_tensor_is_not_counted_as_full_bf16_parameters(self):
        raw = json.dumps({'packed': {'dtype': 'U32', 'shape': [8, 4], 'data_offsets': [0, 128]}}).encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'toy.safetensors'; path.write_bytes(struct.pack('<Q', len(raw)) + raw)
            self.assertNotIn('stored_parameter_elements', safetensors_analysis(path))


if __name__ == '__main__': unittest.main()
