"""Procedural containers/metadata only: no speech, real consent, decoder or WER."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from offline_exchange_guard import audit_audio, audit_pilot, strict_request


class OfflineExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "audio").mkdir()
        (self.root / "annotations").mkdir()
        self.cases = []
        for index, role in enumerate(("clean_target", "codec_target", "no_target")):
            path = "audio/" + str(index) * 64 + ".wav"
            with wave.open(str(self.root / path), "wb") as audio:
                audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                audio.writeframes(bytes([index, 0]) * 80000)
            digest = hashlib.sha256((self.root / path).read_bytes()).hexdigest()
            target = index < 2
            self.cases.append({
                "schema": "RF_RESEARCH_AUDIO_V1", "case_id": "offline-label-" + str(index),
                "session_id": "anonymous-session", "speaker_id": "anonymous-speaker",
                "condition": role, "pilot_role": role, "evidence_class": "MODEL_FREE",
                "split": "control" if not target else "holdout", "cluster_id": "paired" if target else "negative",
                "rights_status": "verified", "research_allowed": True,
                "expected": {"has_target": target, "gold_text": "authored metadata only" if target else "", "verse_ref": ""},
                "channels": [{"role": "close", "path": path, "sha256": digest,
                              "sample_rate": 16000, "samples": 80000, "clock_id": "capture-clock"}],
            })
        self.cases[1].update(parent_case_id=self.cases[0]["case_id"],
                             parent_source_sha256=self.cases[0]["channels"][0]["sha256"])
        for index, case in enumerate(self.cases):
            record = {"origin": "human", "independent_of_asr": True, "adjudicated": True,
                      "transcriber_ids": ["authored-person-a", "authored-person-b"],
                      "source_sha256": case.get("parent_source_sha256", case["channels"][0]["sha256"]),
                      **case["expected"]}
            path = "annotations/" + str(index) + ".json"
            raw = json.dumps(record).encode()
            (self.root / path).write_bytes(raw)
            case["gold_provenance"] = {"annotation_path": path, "annotation_sha256": hashlib.sha256(raw).hexdigest()}
        with (Path(__file__).resolve().parents[1] / "RESEARCH_PRIORITY_AND_EVIDENCE.csv").open(newline="") as handle:
            pins = list(csv.DictReader(handle))
        self.models = [{"id": p["model"], "family": p["family"], "precision": p["precision"], "sha256": p["weight_sha256"]} for p in pins]

    def test_nested_model_and_channel_metadata_are_not_decoder_context(self):
        case, model = copy.deepcopy(self.cases[0]), dict(self.models[0])
        case["channels"][0].update(gold_text="DO_NOT_SEND", speaker_id="DO_NOT_SEND")
        model.update(prompt="DO_NOT_SEND", expected_verse="DO_NOT_SEND", api_key="DO_NOT_SEND")
        request = strict_request(case, model, 1)
        self.assertNotIn("DO_NOT_SEND", json.dumps(request))
        self.assertEqual(set(request["model"]), {"id", "family", "precision", "sha256"})
        self.assertNotIn("expected", request)

    def test_case_and_model_labels_are_opaque_or_canonical_and_copied(self):
        self.cases[0]["case_id"] = "John 3:16 other preacher"
        self.cases[0]["channels"][0]["clock_id"] = "John 3:16 reference clock"
        model = dict(self.models[0], id="John 3:16")
        request = strict_request(self.cases[0], model, 1)
        self.assertNotIn("John", json.dumps(request))
        self.cases[0]["channels"][0]["sha256"] = "f" * 64
        self.assertNotEqual(request["channels"][0]["sha256"], "f" * 64)

    def test_q8_does_not_silently_change_v1_into_the_v2_draft(self):
        with self.assertRaises(ValueError): strict_request(self.cases[0], self.models[2], 1)

    def test_restricted_teacher_and_wrong_pin_are_rejected(self):
        for change in ({"family": "r2t2"}, {"sha256": "f" * 64}):
            with self.assertRaises(ValueError): strict_request(self.cases[0], dict(self.models[0], **change), 1)

    def test_verse_bearing_or_nonopaque_audio_name_rejected(self):
        self.cases[0]["channels"][0]["path"] = "audio/John_3_16.wav"
        with self.assertRaises(ValueError): strict_request(self.cases[0], self.models[0], 1)

    def test_matched_containers_and_sidecars_are_not_asr_or_consent_proof(self):
        result = audit_pilot(self.cases, self.root)
        self.assertTrue(result["integrity_and_declarations_complete"])
        self.assertEqual(result["execution"], "NOT_RUN")
        self.assertEqual(result["human_rights_gold_lineage_review"], "REQUIRED")
        self.assertIsNone(result["real_church_wer_pct"])
        self.assertFalse(result["goal_met"])

    def test_readability_and_pending_rights_are_separate(self):
        self.cases[0]["rights_status"] = "pending"
        row = audit_pilot(self.cases, self.root)["records"][0]
        self.assertEqual(row["rights"], "RIGHTS_PENDING")
        self.assertEqual(row["audio"][0]["access"], "FOUND_READABLE")
        self.cases[0].update(rights_status="verified", research_allowed=False)
        self.assertEqual(audit_pilot(self.cases, self.root)["records"][0]["rights"], "DENIED")

    def test_denied_access_is_not_missing_or_zero_wer(self):
        with patch("offline_exchange_guard.Path.open", side_effect=PermissionError):
            result = audit_audio(self.root, self.cases[0]["channels"][0])
        self.assertEqual(result["access"], "DENIED")
        self.assertFalse(result["integrity"])

    def test_missing_file_and_hash_mismatch_are_explicit(self):
        channel = dict(self.cases[0]["channels"][0], path="audio/missing.wav")
        self.assertEqual(audit_audio(self.root, channel)["access"], "NOT_FOUND")
        channel = dict(self.cases[0]["channels"][0], sha256="f" * 64)
        self.assertEqual(audit_audio(self.root, channel)["reason"], "HASH_MISMATCH")

    def test_gold_sidecar_tampering_and_wrong_control_source_block(self):
        p = self.root / self.cases[0]["gold_provenance"]["annotation_path"]
        p.write_bytes(p.read_bytes() + b" ")
        result = audit_pilot(self.cases, self.root)
        self.assertEqual(result["records"][0]["gold"], "BLOCKED_GOLD")
        self.assertFalse(result["integrity_and_declarations_complete"])
        control = self.cases[2]
        control["parent_source_sha256"] = self.cases[0]["channels"][0]["sha256"]
        path = self.root / control["gold_provenance"]["annotation_path"]
        record = json.loads(path.read_text())
        record["source_sha256"] = control["parent_source_sha256"]
        raw = json.dumps(record).encode(); path.write_bytes(raw)
        control["gold_provenance"]["annotation_sha256"] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(audit_pilot(self.cases, self.root)["records"][2]["gold"], "BLOCKED_GOLD")

    def test_wrong_gold_or_pairing_is_not_accepted_as_matched_codec(self):
        for field, value in (("parent_case_id", "wrong"), ("parent_source_sha256", "f" * 64), ("cluster_id", "wrong")):
            cases = copy.deepcopy(self.cases)
            cases[1][field] = value
            with self.assertRaises(ValueError): audit_pilot(cases, self.root)
        cases = copy.deepcopy(self.cases)
        cases[1]["channels"][0]["samples"] -= 1
        with self.assertRaises(ValueError): audit_pilot(cases, self.root)

    def test_target_absent_cannot_reuse_target_bytes(self):
        self.cases[2]["channels"][0] = dict(self.cases[0]["channels"][0])
        with self.assertRaises(ValueError): audit_pilot(self.cases, self.root)

    def test_symlink_escape_never_reads_external_payload(self):
        source = self.root / self.cases[0]["channels"][0]["path"]
        outside = self.root.parent / (self.root.name + "-outside.wav")
        outside.write_bytes(source.read_bytes())
        self.addCleanup(outside.unlink)
        source.unlink(); source.symlink_to(outside)
        result = audit_audio(self.root, self.cases[0]["channels"][0])
        self.assertFalse(result["integrity"])
        self.assertEqual(result["reason"], "INVALID_OR_UNSAFE_AUDIO")

    def test_truncated_payload_fails_even_if_hash_updated(self):
        channel = dict(self.cases[0]["channels"][0])
        path = self.root / channel["path"]
        raw = path.read_bytes()[:-2]
        path.write_bytes(raw); channel["sha256"] = hashlib.sha256(raw).hexdigest()
        result = audit_audio(self.root, channel)
        self.assertEqual(result["access"], "FOUND_READABLE")
        self.assertFalse(result["integrity"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
