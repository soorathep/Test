"""Generate Week 3 male English narration with exact PCM cue timings.

Run with the absolute research-environment interpreter, for example:
    "$HOME/.venvs/research/bin/python" asynchronous-week03/build-narration.py
Models remain local under tmp/audio/kokoro-models and are not deliverable assets.
"""
from pathlib import Path
import argparse
import hashlib
import html
import importlib.metadata
import json
import re
import textwrap
import time

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parents[1]
SR = 24000
SETTINGS = {
    'engine': 'Kokoro ONNX',
    'engine_version': importlib.metadata.version('kokoro-onnx'),
    'model': 'Kokoro v1.0',
    'voice': 'am_michael',
    'voice_description': 'Michael, male US English',
    'language': 'en-us',
    'speed': .94,
    'sentence_pause': 0,
    'clause_pause': .12,
    'cue_gap_seconds': .18,
    'leading_silence_seconds': .18,
    'trailing_silence_seconds': .35,
    'target_segment_rms': .075,
    'peak_limit': .89,
    'sample_rate': SR,
    'format': 'WAV PCM_16 mono',
    'pronunciation_version': 3,
}
NUMBERS = {
    0:'zero',1:'one',2:'two',3:'three',4:'four',5:'five',6:'six',7:'seven',8:'eight',9:'nine',
    10:'ten',11:'eleven',12:'twelve',13:'thirteen',14:'fourteen',15:'fifteen',16:'sixteen',
    17:'seventeen',18:'eighteen',19:'nineteen',20:'twenty',21:'twenty one',22:'twenty two',
    23:'twenty three',24:'twenty four',25:'twenty five',26:'twenty six',27:'twenty seven',
    28:'twenty eight',29:'twenty nine',30:'thirty',
}

def digest_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def speech_aliases(text):
    # The narration JSON and captions keep the original English text.
    speech = text
    for original, spoken in (
        ('NRTL','N R T L'), ('JSON','J S O N'), ('CSV','C S V'),
        ('VLE','V L E'), ('LLE','L L E'), ('UTF','U T F'), ('XLSX','X L S X'),
    ):
        speech = re.sub(r'\b' + original + r'\b', spoken, speech)
    speech = re.sub(r'\b([A-Z]{1,2})(\d{1,3})\b',
                    lambda m: ' '.join(m[1]) + ' ' + NUMBERS.get(int(m[2]), ' '.join(NUMBERS[int(x)] for x in m[2])), speech)
    speech = speech.replace('Antoine','An-twahn').replace('Raoult','Rah-oolt')
    speech = speech.replace('Gibbs-Duhem', 'Gibbs Doo-em').replace('Gibbs–Duhem', 'Gibbs Doo-em').replace('Margules', 'Mar-goo-less').replace('Padé', 'Pah-day')
    speech = speech.replace('U T F-eight','U T F eight')
    speech = re.sub(r'\bA (?=one\b|two\b|three\b|four\b)', 'A-', speech)
    # A is the Antoine constant, not the indefinite article.
    speech = speech.replace('equal to A minus B', 'equal to A, minus B')
    return speech

def split_sentences(text):
    # Scripts use spelled-out numerical values; periods belong to sentence endings.
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip()) if s.strip()]
    assert ' '.join(sentences) == text.strip(), 'Sentence split changed the original narration.'
    return sentences

def vtt_time(sample):
    milliseconds = (sample * 1000 + SR // 2) // SR
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}'

def main():
    start_clock = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path, default=ROOT/'tmp/audio/kokoro-models')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs/week03-video/audio')
    parser.add_argument('--cache', type=Path, default=ROOT/'tmp/audio/week03-male')
    parser.add_argument('--script', type=Path, default=Path(__file__).with_name('narration.json'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    script_dir = Path(__file__).resolve().parent
    entries = json.loads(args.script.read_text())
    for entry in entries:
        entry.setdefault('id', f"{entry.get('number',entry.get('slide')):02d}")
        entry['narration'] = ' '.join(entry['narration'].split())
    first = int(entries[0]['id'])
    assert [e['id'] for e in entries] == [f'{i:02d}' for i in range(first, first+len(entries))], 'Expected contiguous ordered slides.'
    for entry in entries:
        assert not re.search(r'[\u0e00-\u0e7f]', entry['narration']), 'Narration must be English.'
        assert '\\' not in entry['narration'], 'No raw LaTeX in spoken narration.'
    model_path = args.model_dir/'kokoro-v1.0.onnx'
    voices_path = args.model_dir/'voices-v1.0.bin'
    provenance = {'model_sha256': digest_file(model_path), 'voices_sha256': digest_file(voices_path)}
    engine = None
    chapters, all_cues, qa_segments, master_parts = [], [], [], []
    offset, generated_count, cached_count = 0, 0, 0
    lead, tail, gap = [round(SETTINGS[k] * SR) for k in ('leading_silence_seconds','trailing_silence_seconds','cue_gap_seconds')]
    for entry in entries:
        local_cues, pieces, cursor = [], [np.zeros(lead, dtype=np.float32)], lead
        sentences = split_sentences(entry['narration'])
        for i, sentence in enumerate(sentences):
            cue_id = f"{entry['id']}-{i+1:02d}"
            spoken = speech_aliases(sentence)
            key = hashlib.sha256(json.dumps({'speech':spoken,'settings':SETTINGS,'provenance':provenance},sort_keys=True).encode()).hexdigest()
            cached = args.cache/f'{key}.wav'
            if cached.exists():
                signal, sample_rate = sf.read(cached, dtype='float32')
                cached_count += 1
            else:
                if engine is None:
                    engine = Kokoro(str(model_path),str(voices_path))
                signal, sample_rate = engine.create(spoken, voice=SETTINGS['voice'], speed=SETTINGS['speed'], lang=SETTINGS['language'], sentence_pause=0, clause_pause=SETTINGS['clause_pause'])
                signal = np.asarray(signal, dtype=np.float32)
                assert sample_rate == SR and signal.ndim == 1 and len(signal) > 1000
                sf.write(cached,signal,sample_rate,subtype='FLOAT')
                generated_count += 1
            assert sample_rate == SR and np.isfinite(signal).all()
            assert np.max(np.abs(signal)) > .01, (cue_id,'empty audio')
            cue_start, cue_end = cursor, cursor + len(signal)
            local_cues.append({'id':cue_id,'chapter_id':entry['id'],'text':sentence,
                               'start_sample':offset+cue_start,'end_sample':offset+cue_end,
                               'start_seconds':(offset+cue_start)/SR,'end_seconds':(offset+cue_end)/SR})
            pieces.append(signal)
            cursor = cue_end
            if i < len(sentences)-1:
                pieces.append(np.zeros(gap,dtype=np.float32)); cursor += gap
        pieces.append(np.zeros(tail,dtype=np.float32)); cursor += tail
        segment = np.concatenate(pieces)
        assert len(segment) == cursor
        before_rms = float(np.sqrt(np.mean(segment.astype(np.float64)**2)))
        before_peak = float(np.max(np.abs(segment)))
        rms_gain = SETTINGS['target_segment_rms']/max(before_rms,1e-10)
        peak_gain = SETTINGS['peak_limit']/max(before_peak,1e-10)
        gain = min(rms_gain,peak_gain)
        segment = segment*gain
        filename = f"segment-{entry['id']}.wav"
        output_file = args.output/filename
        sf.write(output_file,segment,SR,subtype='PCM_16')
        # Construct the master from the exact delivered PCM samples.
        delivered, delivered_sr = sf.read(output_file,dtype='int16')
        assert delivered_sr == SR and len(delivered) == cursor
        master_parts.append(delivered)
        value = delivered.astype(np.float64)/32768
        peak = float(np.max(np.abs(value)))
        rms = float(np.sqrt(np.mean(value**2)))
        clipping = int(np.count_nonzero((delivered==32767)|(delivered==-32768)))
        assert clipping == 0 and peak <= SETTINGS['peak_limit']+1/32768
        assert np.count_nonzero(delivered[:lead]) == 0 and np.count_nonzero(delivered[-tail:]) == 0
        chapter = {**entry,'pause_instruction':entry.get('pause_instruction',''),'start_sample':offset,'end_sample':offset+cursor,
                   'start_seconds':offset/SR,'end_seconds':(offset+cursor)/SR,
                   'duration_samples':cursor,'duration_seconds':cursor/SR,
                   'audio':filename,'audio_sha256':digest_file(output_file),
                   'narration_sha256':hashlib.sha256(entry['narration'].encode()).hexdigest(),
                   'cues':local_cues}
        chapters.append(chapter);all_cues.extend(local_cues)
        qa_segments.append({'id':entry['id'],'file':filename,'samples':cursor,'duration_seconds':cursor/SR,
                            'cue_count':len(local_cues),'word_count':len(entry['narration'].split()),
                            'peak':peak,'rms':rms,'gain':gain,'peak_limited':peak_gain<rms_gain,
                            'clipped_samples':clipping,'leading_silence_samples':lead,'trailing_silence_samples':tail,
                            'cue_gap_samples':gap})
        offset += cursor
        print(f"Segment {entry['id']}: {cursor/SR:.3f}s, {len(local_cues)} sentence cues, peak={peak:.4f}, RMS={rms:.4f}",flush=True)
    master = np.concatenate(master_parts)
    assert len(master) == offset
    sf.write(args.output/'master.wav',master,SR,subtype='PCM_16')
    round_trip, round_trip_sr = sf.read(args.output/'master.wav',dtype='int16')
    assert round_trip_sr == SR and np.array_equal(round_trip,master)
    for a,b in zip(chapters,chapters[1:]): assert a['end_sample']==b['start_sample']
    for a,b in zip(all_cues,all_cues[1:]): assert a['end_sample']<b['start_sample']
    for c in chapters:
        assert c['cues'][0]['start_sample']==c['start_sample']+lead
        assert c['cues'][-1]['end_sample']==c['end_sample']-tail
        assert ' '.join(x['text'] for x in c['cues']) == c['narration']
    timeline = {'title':'Week 3: Thermodynamic consistency and liquid stability','sample_rate':SR,'time_base':'1/24000',
                'duration_samples':offset,'duration_seconds':offset/SR,'master':'master.wav',
                'master_sha256':digest_file(args.output/'master.wav'),
                'timing_convention':'End-exclusive integer PCM sample offsets. All sentence cue offsets are absolute in the master.',
                'generation':SETTINGS,'provenance':provenance,'chapters':chapters,'cues':all_cues}
    (args.output/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
    lines=['WEBVTT','','NOTE Sentence cues use the original English narration. Timing derives from exact PCM samples.','']
    for cue in all_cues:
        lines.extend([cue['id'],f"{vtt_time(cue['start_sample'])} --> {vtt_time(cue['end_sample'])}",
                      '\n'.join(textwrap.wrap(html.escape(cue['text'], quote=False),width=70,break_long_words=False,break_on_hyphens=False)),''])
    (args.output/'captions.vtt').write_text('\n'.join(lines).rstrip()+'\n')
    manifest = [{**c, 'slide':int(c['id']), 'generation':SETTINGS} for c in chapters]
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    elapsed = time.monotonic()-start_clock
    master_float = master.astype(np.float64)/32768
    qa = {'passed':True,'sample_rate':SR,'channel_count':1,'format':'PCM_16',
          'duration_samples':offset,'duration_seconds':offset/SR,'chapter_count':len(chapters),
          'cue_count':len(all_cues),'total_words':sum(x['word_count'] for x in qa_segments),
          'runtime_seconds':elapsed,'generated_sentence_count':generated_count,'cached_sentence_count':cached_count,
          'master_peak':float(np.max(np.abs(master_float))),'master_rms':float(np.sqrt(np.mean(master_float**2))),
          'clipped_samples':int(np.count_nonzero((master==32767)|(master==-32768))),
          'checks':[f'{len(entries)} ordered slides','24000 Hz mono PCM_16','Master exactly equals concatenated delivered segments',
                    'Contiguous chapter intervals','Nonoverlapping sentence cues','Cue text reconstructs original narration',
                    '4320-sample lead and 8400-sample tail per chapter','4320-sample gaps between sentence cues',
                    'No clipping; peak <=0.89 within PCM quantization tolerance'],
          'normalization_note':'A single gain normalizes each complete segment toward RMS 0.075. The 0.89 peak ceiling takes priority if both cannot be achieved.',
          'segments':qa_segments}
    (args.output/'audio-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(f'TOTAL {offset} samples / {offset/SR:.6f}s; {len(all_cues)} sentence cues; runtime {elapsed:.1f}s',flush=True)

if __name__ == '__main__':
    main()
