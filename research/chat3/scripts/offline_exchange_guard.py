#!/usr/bin/env python3
"""Read-only pilot intake and strict V1 envelope; never imports/runs an ASR model.

An integrity/attestation check is not independent proof of consent or gold.
The Personal owner supplies an explicitly approved export root; no discovery of
Personal checkouts, weights, recordings, credentials or runtime caches occurs.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import wave

from rf_research_audio import inference_request, validate_case

OPAQUE_AUDIO = re.compile(r"^audio/[a-f0-9]{32,64}\.wav$")
CHANNEL_FIELDS = ("role", "path", "sha256", "sample_rate", "samples", "clock_id")
MODEL_FIELDS = ("id", "family", "precision", "sha256")


def strict_request(case, model, request_id):
    """Keep V1's model rules; drop nested extras and use opaque identifiers.

    This is a separate research profile, not a change to the published V1 or a
    claim that an installed Personal producer/consumer supports this profile.
    Pins identify expected artifacts, not bytes loaded by a verified runtime.
    """
    pins_path = Path(__file__).resolve().parents[1] / "RESEARCH_PRIORITY_AND_EVIDENCE.csv"
    with pins_path.open(newline="") as handle:
        pins = {(p["family"], p["precision"]): p["weight_sha256"] for p in csv.DictReader(handle)}
    if pins.get((model.get("family"), model.get("precision"))) != model.get("sha256"):
        raise ValueError("model does not match a published pilot pin")
    clean_model = {field: model[field] for field in MODEL_FIELDS}
    clean_model["id"] = ":".join(model[field] for field in ("family", "precision", "sha256"))
    result = inference_request(case, clean_model, request_id)
    if any(not OPAQUE_AUDIO.fullmatch(c["path"]) for c in result["channels"]):
        raise ValueError("strict profile requires opaque audio/<hex>.wav paths")
    result["case_id"] = hashlib.sha256(case["case_id"].encode()).hexdigest()[:24]
    result["channels"] = [{key: channel[key] for key in CHANNEL_FIELDS}
                          for channel in result["channels"]]
    for channel in result["channels"]:
        channel["clock_id"] = hashlib.sha256(channel["clock_id"].encode()).hexdigest()[:24]
    return result


def checked_path(root, relative):
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError("relative export path required")
    root = Path(root).resolve()
    resolved = (root / relative).resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("export symlink escapes approved root")
    return resolved


def audit_audio(root, channel):
    """Hash and inspect the same open descriptor; report access separately."""
    result = {"role": channel["role"], "access": "NOT_PROVIDED", "integrity": False}
    try:
        path = checked_path(root, channel["path"])
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
            result.update(access="FOUND_READABLE", observed_sha256=digest)
            if digest != channel["sha256"]:
                result["reason"] = "HASH_MISMATCH"
                return result
            handle.seek(0)
            with wave.open(handle, "rb") as audio:
                rate, frames = audio.getframerate(), audio.getnframes()
                if (audio.getnchannels(), audio.getsampwidth(), rate, frames) != (
                        1, 2, channel["sample_rate"], channel["samples"]):
                    raise ValueError("WAV header does not match mono PCM16 declaration")
                if not 5 <= frames / rate <= 15:
                    raise ValueError("pilot clips must be 5-15 seconds")
                observed_bytes = 0
                while chunk := audio.readframes(65536):
                    observed_bytes += len(chunk)
                if observed_bytes != frames * 2:
                    raise ValueError("truncated PCM payload")
                result.update(integrity=True, sample_rate=rate, samples=frames)
    except PermissionError:
        result.update(access="DENIED", reason="PERMISSION_DENIED")
    except FileNotFoundError:
        result.update(access="NOT_FOUND", reason="FILE_NOT_FOUND")
    except (ValueError, OSError, wave.Error, EOFError):
        # Avoid emitting absolute paths, content or environment details.
        result["reason"] = "INVALID_OR_UNSAFE_AUDIO"
    return result


def audit_gold(root, case):
    """Check sidecar bytes/linkage, not the truth or identity of its authors."""
    provenance = case.get("gold_provenance", {})
    try:
        path = checked_path(root, provenance.get("annotation_path", ""))
        with path.open("rb") as handle:
            raw = handle.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024 or hashlib.sha256(raw).hexdigest() != provenance.get("annotation_sha256"):
            return "BLOCKED_GOLD"
        record = json.loads(raw)
        people = record.get("transcriber_ids", [])
        source = (case.get("parent_source_sha256") if case.get("pilot_role") == "codec_target"
                  else case["channels"][0]["sha256"])
        complete = (record.get("origin") == "human"
                    and record.get("independent_of_asr") is True
                    and record.get("adjudicated") is True
                    and isinstance(people, list) and all(isinstance(p, str) and p for p in people)
                    and len(set(people)) >= 2
                    and record.get("source_sha256") == source
                    and type(record.get("has_target")) is bool
                    and record.get("has_target") == case["expected"]["has_target"]
                    and record.get("gold_text") == case["expected"]["gold_text"])
        return "MATCHED_INDEPENDENT_DECLARATION" if complete else "BLOCKED_GOLD"
    except PermissionError:
        return "DENIED"
    except (FileNotFoundError, ValueError, OSError, TypeError, AttributeError):
        return "BLOCKED_GOLD"


def audit_pilot(cases, root):
    """Assess only owner-exported metadata/audio; never grants execution rights."""
    if len(cases) != 3 or len({c["case_id"] for c in cases}) != 3:
        raise ValueError("exactly three distinct pilot cases required")
    roles = {c.get("pilot_role"): c for c in cases}
    if set(roles) != {"clean_target", "codec_target", "no_target"}:
        raise ValueError("pilot needs clean target, paired codec, target-absent control")
    clean, codec, control = (roles[r] for r in ("clean_target", "codec_target", "no_target"))
    for case in cases:
        validate_case(case)
    if not (clean["expected"]["has_target"] and codec["expected"]["has_target"]
            and not control["expected"]["has_target"]):
        raise ValueError("target/control labels do not match pilot roles")
    if (codec.get("parent_case_id") != clean["case_id"]
            or codec.get("parent_source_sha256") != clean["channels"][0]["sha256"]
            or codec["expected"]["gold_text"] != clean["expected"]["gold_text"]
            or [(c["role"], c["sample_rate"], c["samples"], c["clock_id"]) for c in codec["channels"]]
            != [(c["role"], c["sample_rate"], c["samples"], c["clock_id"]) for c in clean["channels"]]
            or codec.get("cluster_id") != clean.get("cluster_id")
            or not clean.get("cluster_id")):
        raise ValueError("codec source/gold/cluster mismatch")
    if control["channels"][0]["sha256"] in {c["channels"][0]["sha256"] for c in (clean, codec)}:
        raise ValueError("target-absent control cannot reuse target audio")
    records = []
    for case in cases:
        rights = ("VERIFIED_DECLARATION" if case["rights_status"] == "verified"
                  and case["research_allowed"] else
                  "DENIED" if case["rights_status"] == "denied"
                  or case["research_allowed"] is False else "RIGHTS_PENDING")
        records.append({"pilot_role": case["pilot_role"], "rights": rights,
                        "gold": audit_gold(root, case),
                        "audio": [audit_audio(root, channel) for channel in case["channels"]],
                        "execution": "NOT_RUN"})
    complete = all(r["rights"] == "VERIFIED_DECLARATION"
                   and r["gold"] == "MATCHED_INDEPENDENT_DECLARATION"
                   and all(a["integrity"] for a in r["audio"]) for r in records)
    return {"schema": "RF_CHAT3_PILOT_INTAKE_V1", "records": records,
            "integrity_and_declarations_complete": complete,
            "human_rights_gold_lineage_review": "REQUIRED",
            "codec_transform_independently_verified": False,
            "model_bytes_runtime_verified": False,
            "asr_execution_authorized": False,
            "execution": "NOT_RUN", "models_loaded": 0,
            "real_church_wer_pct": None, "goal_met": False,
            "production": "PRODUCTION_NO_GO"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="approved offline export directory")
    parser.add_argument("--cases", type=Path, required=True, help="operator/scorer V1 case array")
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text())
    print(json.dumps(audit_pilot(cases, args.root), indent=2))


if __name__ == "__main__":
    main()
