"""Cached ASR/source comparison for the new Week 4 opening and patched core.

Run with ~/.venvs/research/bin/python. Uses only the existing local tiny.en
cache, one CPU thread, and no download. Missing or changing WAVs remain pending.
Manual source-comparison decisions are tied to exact audio and narration hashes
in qa-audio-reviews.json. ASR alone never establishes subjective audio quality.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPT = HERE / "narration.json"
OUTPUT = ROOT / "outputs/week04-opening-video"
WAVS = OUTPUT / "audio"
MANIFEST = WAVS / "manifest.json"
REPORT = OUTPUT / "asr-review.json"
CACHE = OUTPUT / "asr-cache"
REVIEWS = HERE / "qa-audio-reviews.json"
MODEL_CACHE = ROOT / "tmp/audio/whisper-model"
TARGETS = list(range(1, 15)) + [15, 17, 49, 50]
FOCUS = {
    1: "No repeat reading; four-minute R1-R3 notebook work; H optional; A-G and I; no extra submission.",
    2: "Consistency, modeling capability and phase stability need different evidence.",
    3: "Dimensionless excess Gibbs quantity; product rule; fixed-T/P Gibbs-Duhem; neglected pressure term and variable-T correction.",
    4: "Positive magnitude A-minus; normalized absolute area difference; D below 5%; not every-point percentage error; undefined zero denominator.",
    5: "r = derivative of excess g minus ln(gamma1/gamma2); score 100 mean absolute r; score below 5 dimensionless, not percent; local peak can remain.",
    6: "350 K, amplitude .25, 81 points; D 1.956%, score 1.591, r(.35) about -.250; 41 to 161 same synthetic function, not new measurements.",
    7: "Consistent NRTL joint P/y fit; relative P error vs absolute y difference; below 1% and 1 percentage point; no certification.",
    8: "Total mixing g versus excess-only gE; x trial composition versus z feed; fixed T/P; composition not time.",
    9: "Amber homogeneous curve/diamond; graphite tangent; dashed teal envelope/circle; contacts .07072/.92928 are compositions, not amounts.",
    10: "Curvature 1/x+1/(1-x)-2A; z=.12 gives positive 3.4697; local not global; negative unstable; zero needs examination.",
    11: "Lever fractions .057398/.942602; conserved z=.12; gone -.050125 vs gsplit -.058341; positive displayed energy reduction .00821636, measured in RT/mol (precise number need not be spoken); metastable.",
    12: "Global support g-line nonnegative everywhere; binodal residual not global support; negative feed TPD rejects global stability; z=.35 gives fbeta .325289 and negative curvature.",
    13: "Four-minute R1-R3 pause; R1 every-point inference, R2 positive curvature/lower split, R3 z=.35 fractions and balances.",
    14: "R1 no, R2 metastable, R3 .325289/.674711; A-G/I required, H optional; single existing form.",
    15: "Bridge to core lesson after opening, no separate submission; existing Session 4 form once.",
    17: "Opening already completed; no repeat reading; 100 remaining required work minutes, 10-minute break; H optional +20.",
    49: "H explicitly optional; required route skips to exit; optional GSE 310K/2L/5kPa, .002/.008 volatile, .001 inert; adsorption qs3/b.05/P20/T310/V2L/m5g.",
    50: "Explicit route choice; optional H adds 20 minutes; GSE/adsorption inventory checks; no exact new pressure required.",
}
SETTINGS = {"model":"tiny.en","device":"cpu","compute_type":"int8","cpu_threads":1,
            "num_workers":1,"beam_size":3,"language":"en","local_files_only":True}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(report):
    report["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    temporary = REPORT.with_suffix(".tmp.json")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(REPORT)


def main():
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from faster_whisper import WhisperModel
    entries = json.loads(SCRIPT.read_text())
    assert len(entries) == 54 and [e["slide"] for e in entries] == list(range(1,55))
    source_hash = sha(SCRIPT)
    settings = {**SETTINGS,"faster_whisper_version":importlib.metadata.version("faster-whisper")}
    settings_hash = hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()
    reviews = json.loads(REVIEWS.read_text()) if REVIEWS.exists() else {}
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else None
    if manifest is not None:
        assert len(manifest)==54
    CACHE.mkdir(parents=True, exist_ok=True)
    ready = [n for n in TARGETS if (WAVS/f"segment-{n:02d}.wav").exists()]
    pending = [n for n in TARGETS if n not in ready]
    report = {"method":settings,"scope":"All 14 new opening tracks and four patched core tracks; cached ASR plus manual comparison to exact script. Not full subjective listening.",
              "script_sha256":source_hash,"manifest_sha256":sha(MANIFEST) if manifest else None,
              "targets":TARGETS,"status":"partial" if pending else "pending_source_comparison",
              "pending_audio":pending,"checks":[],"limitations":["Tiny ASR can misrecognize scientific names, letters and spoken decimals.","Only clear possible semantic changes are flagged for targeted listening.","A source comparison does not establish full subjective listening or naturalness."]}
    model = None
    for number in ready:
        if sha(SCRIPT)!=source_hash:
            raise RuntimeError("Script changed during ASR; rerun the helper.")
        entry = entries[number-1]
        wav = WAVS/f"segment-{number:02d}.wav"
        before = sha(wav)
        narration_hash = hashlib.sha256(" ".join(entry["narration"].split()).encode()).hexdigest()
        if manifest:
            track=manifest[number-1]
            assert track["audio_sha256"]==before and track["narration_sha256"]==narration_hash
        cache_path = CACHE/f"{before}-{settings_hash[:12]}.json"
        if cache_path.exists():
            result=json.loads(cache_path.read_text())
            assert result["audio_sha256"]==before and result["settings"]==settings
            cached=True
        else:
            signal, rate=sf.read(wav)
            if signal.ndim>1:signal=signal.mean(axis=1)
            if len(signal)<1000 or sha(wav)!=before:
                report["pending_audio"].append(number)
                continue
            divisor=math.gcd(rate,16000)
            pcm=resample_poly(signal,16000//divisor,rate//divisor).astype(np.float32)
            if model is None:
                if not MODEL_CACHE.is_dir():raise RuntimeError("Existing local model cache is unavailable; no download attempted.")
                model=WhisperModel("tiny.en",device="cpu",compute_type="int8",download_root=str(MODEL_CACHE),local_files_only=True,cpu_threads=1,num_workers=1)
            segments,info=model.transcribe(pcm,language="en",beam_size=3)
            segments=[{"start":s.start,"end":s.end,"text":s.text.strip()} for s in segments]
            if sha(wav)!=before:
                report["pending_audio"].append(number)
                continue
            result={"audio_sha256":before,"settings":settings,"recognized":" ".join(s["text"] for s in segments),"segments":segments,
                    "duration_seconds":len(signal)/rate,"sample_rate":rate,"peak":float(np.max(np.abs(signal))),
                    "clipped_samples":int(np.count_nonzero(np.abs(signal)>=.9999))}
            cache_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
            cached=False
        manual=reviews.get(str(number),{})
        if manual.get("audio_sha256")!=before or manual.get("narration_sha256")!=narration_hash:
            manual={"status":"pending_source_comparison","note":"Compare recognized text and source; do not classify ASR spelling alone as an audio defect."}
        check={"slide":number,"core_slide":entry.get("core_slide"),"title":entry["title"],"focus":FOCUS[number],
               "audio_file":wav.name,"audio_sha256":before,"narration_sha256":narration_hash,
               "expected_narration":entry["narration"],**{k:v for k,v in result.items() if k not in ("audio_sha256","settings")},
               "cached_transcription":cached,"manual_source_comparison":manual}
        report["checks"].append(check)
        save(report)
        print(f"Track {number:02d}: {'cached' if cached else 'transcribed'}, {result['duration_seconds']:.1f}s, review {manual['status']}",flush=True)
    pending_review=[c["slide"] for c in report["checks"] if c["manual_source_comparison"]["status"]=="pending_source_comparison"]
    flags=[c["slide"] for c in report["checks"] if c["manual_source_comparison"]["status"]=="possible_audio_issue"]
    report["pending_source_comparison"]=pending_review
    report["targeted_listening_needed"]=flags
    report["status"]="partial" if report["pending_audio"] else "pending_source_comparison" if pending_review else "targeted_listening_needed" if flags else "reviewed_no_clear_semantic_mismatch"
    save(report)
    print(json.dumps({"status":report["status"],"checked":len(report["checks"]),"pending_audio":report["pending_audio"],"pending_source_comparison":pending_review,"targeted_listening_needed":flags}),flush=True)


if __name__=="__main__":
    main()
