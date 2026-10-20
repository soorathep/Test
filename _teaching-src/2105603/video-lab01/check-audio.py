"""ASR spot checks gated on the final 14-chapter audio manifest and script.

Run with the absolute research interpreter. The cached tiny.en model is used
with local_files_only=True; this script never requests a model download.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "asynchronous-lab01/narration.json"
FOLDER = BASE / "outputs/lab01-video/audio"
MANIFEST = FOLDER / "manifest.json"
REPORT = FOLDER / "spot-check-transcripts.json"
TARGETS = [2, 4, 6, 7, 12, 14]
ACTIVITY_MINUTES = {3: 2, 13: 5}
FOCUS = {
    2: "Ideal synthetic system at T350 K, P95 kPa, z1 .5; saturation pressures150/60 kPa; one-mole feed basis.",
    4: "Bubble x=z=.5 gives105 kPa; dew y=z=.5 gives85.714 kPa; these are not current tie-line endpoint compositions.",
    6: "Separate A and B component balances on one-mole feed basis; phase amounts sum to1; retain precision.",
    7: "Dimensionless K=Psat/P; Rachford-Rice endpoint signs and beta root; composition versus amount axes.",
    12: "Comparison JSON download and reopening; restore selected saved case and calculate fresh current results.",
    14: "Independent90kPa check: x1=1/3,y1=5/9,beta=3/4; phase amounts1/4 and3/4 mol; both component sums=.5 mol.",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(text):
    return " ".join(text.split())


def ready():
    if not SCRIPT.exists() or not MANIFEST.exists():
        raise ValueError("Final narration or audio manifest is not available.")
    entries = json.loads(SCRIPT.read_text())
    entries = entries["slides"] if isinstance(entries, dict) else entries
    tracks = json.loads(MANIFEST.read_text())
    if not isinstance(tracks, list) or len(tracks) != 14 or len(entries) != 14:
        raise ValueError(f"Expected 14 entries in both files: script={len(entries)}, manifest={len(tracks)}.")
    if [x["number"] for x in entries] != list(range(1, 15)):
        raise ValueError("Narration does not contain ordered chapters 1-14.")
    if [x["number"] for x in tracks] != list(range(1, 15)):
        raise ValueError("Audio manifest does not contain ordered chapters 1-14.")
    for entry, track in zip(entries, tracks):
        number = entry["number"]
        minutes = ACTIVITY_MINUTES.get(number, 0)
        for row in (entry, track):
            if row.get("activity_minutes") != minutes or row.get("activity") != (minutes > 0):
                raise ValueError(f"Chapter {number}: stale activity contract; expected {minutes} minutes.")
        text = normalized(entry["narration"])
        if track["slide_id"] != entry["slide_id"] or normalized(track["narration"]) != text:
            raise ValueError(f"Chapter {entry['number']}: manifest content differs from final narration.")
        if track["narration_sha256"] != hashlib.sha256(text.encode()).hexdigest():
            raise ValueError(f"Chapter {entry['number']}: narration hash mismatch.")
        wav = FOLDER / track["audio"]
        if not wav.exists() or sha(wav) != track["audio_sha256"]:
            raise ValueError(f"Chapter {entry['number']}: final WAV is missing or its hash differs.")
    return entries, tracks, sha(SCRIPT), sha(MANIFEST)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        entries, tracks, script_hash, manifest_hash = ready()
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"NOT READY: {error}", flush=True)
        return 2
    print("READY: all 14 final narration entries and WAV hashes match.", flush=True)
    if args.validate_only:
        return 0

    from faster_whisper import WhisperModel
    from scipy.signal import resample_poly
    import numpy as np
    import soundfile as sf

    cache = BASE / "tmp/audio/whisper-model"
    if not cache.is_dir():
        raise RuntimeError("Local faster-whisper model cache is unavailable; no download attempted.")
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8",
                         download_root=str(cache), local_files_only=True, cpu_threads=1, num_workers=1)
    checks = []
    report = {
        "revision": "Final 14-chapter Lab 01 ideal VLE screen demonstration",
        "method": "Local faster-whisper tiny.en, CPU int8, one thread, beam size 3; model download disabled.",
        "scope": "ASR spot check with source comparison, not a complete subjective listening review.",
        "script_sha256": script_hash,
        "manifest_sha256": manifest_hash,
        "all_14_script_and_wav_hashes_verified": True,
        "targets": TARGETS,
        "status": "in_progress",
        "checks": checks,
    }
    for number in TARGETS:
        if sha(SCRIPT) != script_hash or sha(MANIFEST) != manifest_hash:
            raise RuntimeError("Final source changed during ASR; rerun against the finalized revision.")
        entry, track = entries[number - 1], tracks[number - 1]
        wav = FOLDER / track["audio"]
        if sha(wav) != track["audio_sha256"]:
            raise RuntimeError(f"Chapter {number} WAV changed before transcription.")
        audio, sample_rate = sf.read(wav)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        divisor = math.gcd(sample_rate, 16000)
        pcm = resample_poly(audio, 16000 // divisor, sample_rate // divisor).astype(np.float32)
        segments, info = model.transcribe(pcm, language="en", beam_size=3)
        segments = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
        text = " ".join(s["text"] for s in segments)
        if sha(wav) != track["audio_sha256"]:
            raise RuntimeError(f"Chapter {number} WAV changed during transcription.")
        checks.append({
            "slide": number, "slide_id": entry["slide_id"], "title": entry["title"],
            "focus": FOCUS[number], "audio_file": wav.name,
            "sha256": track["audio_sha256"], "narration_sha256": track["narration_sha256"],
            "duration_seconds": len(audio) / sample_rate, "sample_rate": sample_rate,
            "peak": float(np.max(np.abs(audio))),
            "clipped_samples": int(np.count_nonzero(np.abs(audio) >= .9999)),
            "expected_narration": entry["narration"], "recognized": text,
            "segments": segments, "review_status": "pending_source_comparison",
        })
        report["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
        temp = REPORT.with_suffix(".json.tmp")
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        temp.replace(REPORT)
        print(f"Chapter {number} ({len(audio) / sample_rate:.2f}s): {text}", flush=True)
    ready()
    report["status"] = "transcribed_pending_source_comparison"
    report["limitations"] = [
        "Speech recognition can misrecognize scientific names and spoken numbers; disagreements require source comparison or listening.",
        f"{len(TARGETS)} selected chapters were transcribed, not the whole 14-chapter recording.",
        "No complete subjective listening review is claimed.",
    ]
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved final-WAV spot checks: {REPORT}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
