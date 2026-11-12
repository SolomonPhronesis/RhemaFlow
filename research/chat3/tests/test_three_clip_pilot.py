#!/usr/bin/env python3
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_three_clip_pilot import prepare, read_pcm, sha


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[4])
        self.root = Path(self.temp.name); self.source = self.root/'procedural.wav'
        with wave.open(str(self.source), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
            w.writeframes((np.sin(2*np.pi*220*np.arange(6400)/16000)*4000).astype('<i2').tobytes())
        self.rights = {'rights_status': 'verified', 'research_allowed': True,
                       'source_sha256': sha(self.source), 'gold_text': 'unit test metadata, no spoken words'}

    def tearDown(self): self.temp.cleanup()

    def test_pending_rights_do_not_create_output(self):
        self.rights['rights_status'] = 'pending'
        with self.assertRaises(ValueError): prepare(self.source, self.rights, self.root/'out')
        self.assertFalse((self.root/'out').exists())

    def test_source_hash_mismatch_is_rejected(self):
        self.rights['source_sha256'] = '0'*64
        with self.assertRaises(ValueError): prepare(self.source, self.rights, self.root/'out')

    def test_disk_floor_blocks_preparation(self):
        with patch('prepare_three_clip_pilot.shutil.disk_usage', return_value=shutil._ntuple_diskusage(20*1024**3, 13*1024**3, 7*1024**3)):
            with self.assertRaisesRegex(ValueError, 'BLOCKED_DISK'): prepare(self.source, self.rights, self.root/'out')

    @unittest.skipUnless(shutil.which('ffmpeg'), 'existing ffmpeg required; no installation')
    def test_procedural_roundtrip_preserves_pairing_without_models(self):
        # A model-free media unit test with a mocked resource gate; not a real
        # speech fixture or an ASR checkpoint. Temporary audio is deleted.
        with patch('prepare_three_clip_pilot.shutil.disk_usage', return_value=shutil._ntuple_diskusage(20*1024**3, 4*1024**3, 16*1024**3)):
            cases = prepare(self.source, self.rights, self.root/'out')
        self.assertEqual(len(cases), 3)
        for case in cases:
            channel = case['channels'][0]; p = self.root/'out'/channel['path']
            self.assertEqual(channel['sha256'], sha(p)); self.assertEqual(channel['samples'], 6400)
        result = json.loads((self.root/'out/preparation.json').read_text())
        self.assertEqual(result['models_run'], [])
        self.assertIsNone(result['asr_wer'])


if __name__ == '__main__': unittest.main(verbosity=2)
