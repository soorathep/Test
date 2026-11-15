"""Build per-slide narration in English and Thai (MP3) with caption cues for a 2105315 deck.

    python3 build_narration.py s01 --models /path/to/kokoro-models [--only en|th]

Reads <session>-narration.json and writes
  narration/<session>/<slide-id>.en.mp3 and .th.mp3
  narration/<session>.json   (per slide: sentence texts, and cue times for each voice)

English: Kokoro v1.0, voice am_michael (the same voice as the 2105603 decks).
Thai: Meta MMS-TTS Thai (facebook/mms-tts-tha, CC BY-NC 4.0), a placeholder until the
instructor records his own voice. The Thai model reads Thai script only, so each sentence
carries "th_say" with English terms written as they sound and numbers in words; the script
maps sara am to nikhahit + sara aa (the model has no sara am) and stops on any other
character the model cannot read.

To use a recorded voice later: put <slide-id>.th.mp3 files in narration/<session>/ and run
with --only en --keep-th; Thai cue times are then spread over the recording by sentence length.
"""
from pathlib import Path
import argparse
import json
import subprocess
import tempfile

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
GAP = 0.35            # silence between sentences, s
LEAD, TAIL = 0.25, 0.6


def write_mp3(audio, sr, path):
    with tempfile.NamedTemporaryFile(suffix='.wav') as wav:
        sf.write(wav.name, audio, sr, subtype='PCM_16')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav.name, '-ac', '1', '-b:a', '64k', str(path)], check=True)


def assemble(clips, sr):
    """Join sentence clips with gaps; return audio and (start, end) per sentence."""
    parts, cues, t = [np.zeros(int(LEAD * sr), dtype=np.float32)], [], LEAD
    for clip in clips:
        clip = clip.astype(np.float32)
        clip *= min(1.0, 0.89 / (float(np.max(np.abs(clip))) or 1.0))
        cues.append([round(t, 2), round(t + len(clip) / sr, 2)])
        parts += [clip, np.zeros(int(GAP * sr), dtype=np.float32)]
        t += len(clip) / sr + GAP
    parts.append(np.zeros(int(TAIL * sr), dtype=np.float32))
    return np.concatenate(parts), cues


class English:
    sr = 24000

    def __init__(self, models, voice):
        from kokoro_onnx import Kokoro
        self.k, self.voice = Kokoro(str(Path(models) / 'kokoro-v1.0.onnx'), str(Path(models) / 'voices-v1.0.bin')), voice

    def say(self, text):
        audio, sr = self.k.create(text, voice=self.voice, speed=0.94, lang='en-us')
        assert sr == self.sr
        return audio


class Thai:
    def __init__(self):
        import torch
        from transformers import VitsModel, AutoTokenizer
        self.torch = torch
        self.model = VitsModel.from_pretrained('facebook/mms-tts-tha').eval()
        self.tok = AutoTokenizer.from_pretrained('facebook/mms-tts-tha')
        self.sr = self.model.config.sampling_rate
        self.vocab = set(self.tok.get_vocab())

    def prepare(self, text):
        text = text.replace('ำ', 'ํา')          # sara am -> nikhahit + sara aa
        bad = sorted({c for c in text if c not in self.vocab})
        if bad:
            raise SystemExit(f'Thai voice cannot read {bad!r} in: {text}')
        return text

    def say(self, text):
        self.torch.manual_seed(1)                               # same audio on every build
        inputs = self.tok(self.prepare(text), return_tensors='pt')
        with self.torch.no_grad():
            return self.model(**inputs).waveform[0].numpy()


def spread(n_chars, duration):
    """Cue times for a recording without sentence marks: share the time by sentence length."""
    total = sum(n_chars) or 1
    usable = duration - LEAD - TAIL
    cues, t = [], LEAD
    for n in n_chars:
        d = usable * n / total
        cues.append([round(t, 2), round(t + d, 2)]); t += d
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('session')
    ap.add_argument('--models', default=str(HERE / 'kokoro-models'))
    ap.add_argument('--only', choices=['en', 'th'])
    ap.add_argument('--keep-th', action='store_true', help='keep existing Thai MP3s (a recorded voice)')
    args = ap.parse_args()
    spec = json.loads((HERE / f'{args.session}-narration.json').read_text())
    out_dir = HERE / 'narration' / args.session
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = HERE / 'narration' / f'{args.session}.json'
    old = json.loads(index_path.read_text()) if index_path.exists() else {}
    en = English(args.models, spec.get('voice_en', 'am_michael')) if args.only != 'th' else None
    th = Thai() if args.only != 'en' and not args.keep_th else None
    index = {}
    for slide_id, sentences in spec['slides'].items():
        entry = {'text': [{'en': s['en'], 'th': s['th']} for s in sentences]}
        if en:
            audio, cues = assemble([en.say(s.get('say', s['en'])) for s in sentences], en.sr)
            write_mp3(audio, en.sr, out_dir / f'{slide_id}.en.mp3')
            entry['en'] = {'audio': f'narration/{args.session}/{slide_id}.en.mp3', 'cues': cues}
        elif slide_id in old and 'en' in old[slide_id]:
            entry['en'] = old[slide_id]['en']
        if th:
            audio, cues = assemble([th.say(s['th_say']) for s in sentences], th.sr)
            write_mp3(audio, th.sr, out_dir / f'{slide_id}.th.mp3')
            entry['th'] = {'audio': f'narration/{args.session}/{slide_id}.th.mp3', 'cues': cues}
        elif args.keep_th and (out_dir / f'{slide_id}.th.mp3').exists():
            mp3 = out_dir / f'{slide_id}.th.mp3'
            dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(mp3)],
                                       capture_output=True, text=True, check=True).stdout)
            entry['th'] = {'audio': f'narration/{args.session}/{slide_id}.th.mp3', 'cues': spread([len(s['th']) for s in sentences], dur)}
        elif slide_id in old and 'th' in old[slide_id]:
            entry['th'] = old[slide_id]['th']
        index[slide_id] = entry
        lengths = {k: entry[k]['cues'][-1][1] for k in ('en', 'th') if k in entry}
        print(slide_id, ' '.join(f'{k} {v:.1f}s' for k, v in lengths.items()))
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
