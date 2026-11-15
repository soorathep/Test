"""Build per-slide English narration (MP3) and EN/TH caption cues for a 2027 deck.

    python3 build_narration.py s01 --models /path/to/kokoro-models

Reads <session>-narration.json, writes narration/<session>/<slide-id>.mp3 and
narration/<session>.json (cue times per sentence, English and Thai captions).
Each sentence may carry "say" (what the voice reads) when it differs from the
English caption ("en"), for example numbers and units.
Kokoro v1.0 with the am_michael voice, the same voice as the Lab 01 video.
"""
from pathlib import Path
import argparse
import json
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).resolve().parent
SR = 24000
SPEED = 0.94
GAP = 0.35        # silence between sentences, s
LEAD, TAIL = 0.25, 0.6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('session')
    ap.add_argument('--models', default=str(HERE / '../tmp/kokoro-models'))
    ap.add_argument('--only', nargs='*', help='rebuild only these slide ids')
    args = ap.parse_args()
    models = Path(args.models)
    kokoro = Kokoro(str(models / 'kokoro-v1.0.onnx'), str(models / 'voices-v1.0.bin'))
    spec = json.loads((HERE / f'{args.session}-narration.json').read_text())
    out_dir = HERE / 'narration' / args.session
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = HERE / 'narration' / f'{args.session}.json'
    index = json.loads(index_path.read_text()) if args.only and index_path.exists() else {}
    for slide_id, sentences in spec['slides'].items():
        if args.only and slide_id not in args.only:
            continue
        parts, cues, t = [np.zeros(int(LEAD * SR), dtype=np.float32)], [], LEAD
        for s in sentences:
            audio, sr = kokoro.create(s.get('say', s['en']), voice=spec.get('voice', 'am_michael'), speed=SPEED, lang='en-us')
            assert sr == SR
            audio = audio.astype(np.float32)
            peak = float(np.max(np.abs(audio))) or 1.0
            audio = audio * min(1.0, 0.89 / peak)
            cues.append({'start': round(t, 2), 'end': round(t + len(audio) / SR, 2), 'en': s['en'], 'th': s['th']})
            parts += [audio, np.zeros(int(GAP * SR), dtype=np.float32)]
            t += len(audio) / SR + GAP
        parts.append(np.zeros(int(TAIL * SR), dtype=np.float32))
        mp3 = out_dir / f'{slide_id}.mp3'
        with tempfile.NamedTemporaryFile(suffix='.wav') as wav:
            sf.write(wav.name, np.concatenate(parts), SR, subtype='PCM_16')
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav.name, '-ac', '1', '-b:a', '64k', str(mp3)], check=True)
        index[slide_id] = {'audio': f'narration/{args.session}/{slide_id}.mp3', 'cues': cues}
        print(slide_id, f'{t:.1f} s', len(cues), 'cues')
    index = {k: index[k] for k in spec['slides'] if k in index}
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
