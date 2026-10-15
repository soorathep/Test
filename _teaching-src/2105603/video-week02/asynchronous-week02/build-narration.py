"""Build slide-numbered English narration with local Kokoro ONNX.
Run with the research interpreter. Supply --model-dir if models are elsewhere.
Model weights are kept out of the deliverable. No credentials are required.
"""
from pathlib import Path
import subprocess,json,re,hashlib,csv,html,zipfile,argparse,importlib.metadata
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--model-dir',type=Path,default=ROOT/'tmp/audio/kokoro-models')
args=parser.parse_args()
OUT=ROOT/'output/audio/week02'
TMP=ROOT/'tmp/audio/week02-male'
TMP.mkdir(parents=True,exist_ok=True)
(OUT/'narration').mkdir(parents=True,exist_ok=True)
(OUT/'scripts').mkdir(parents=True,exist_ok=True)
VOICE='am_michael';SPEED=.94
SETTINGS={'engine':'Kokoro ONNX','engine_version':importlib.metadata.version('kokoro-onnx'),
    'model':'Kokoro v1.0','voice':VOICE,'voice_description':'Michael, male US English',
    'language':'en-us','speed':SPEED,'sentence_pause':.4,'clause_pause':.12,
    'target_rms':.075,'peak_limit':.89,'leading_silence':.18,'trailing_silence':.35,
    'pronunciation_version':1}
engine=None
entries=json.loads((ROOT/'asynchronous-week02/narration.json').read_text())
assert [e['slide'] for e in entries]==list(range(1,29))
rows=[]
for e in entries:
    number=e['slide'];stem=f'slide-{number:02d}'
    text=e['narration'].strip()
    assert len(text)>80 and not re.search(r'[\u0e00-\u0e7f]',text)
    speech=text
    for old,new in [('NRTL','N R T L'),('JSON','J S O N'),('CSV','C S V'),('VLE','V L E')]:
        speech=re.sub(r'\b'+old+r'\b',new,speech)
    # These aliases fix the default phonemizer without altering scientific spelling
    # in the editable scripts, transcripts, or slides.
    speech=speech.replace('Antoine','An-twahn').replace('Raoult', 'Rah-oolt')
    # Prevent the phonemizer from treating the worksheet label or constant A
    # as the indefinite article. Hyphenation retains the spoken letter name.
    speech=re.sub(r'\bA (?=one\b|two\b|three\b|four\b)', 'A-', speech)
    speech=speech.replace('Section A begins', 'Section A, begins').replace('is A minus B', 'is A, minus B')
    script=OUT/'scripts'/f'{stem}.txt';script.write_text(text+'\n')
    spoken=TMP/f'{stem}.txt';spoken.write_text(speech+'\n')
    raw=TMP/f'{stem}.wav';audio=OUT/'narration'/f'{stem}.m4a'
    digest=hashlib.sha256((speech+json.dumps(SETTINGS,sort_keys=True)).encode()).hexdigest()
    stamp=TMP/f'{stem}.sha256'
    if not (audio.exists() and raw.exists() and stamp.exists() and stamp.read_text()==digest):
        if engine is None:
            engine=Kokoro(str(args.model_dir/'kokoro-v1.0.onnx'),str(args.model_dir/'voices-v1.0.bin'))
        samples,sample_rate=engine.create(speech,voice=VOICE,speed=SPEED,lang='en-us',
            sentence_pause=SETTINGS['sentence_pause'],clause_pause=SETTINGS['clause_pause'])
        level=float(np.sqrt(np.mean(samples**2)))
        gain=min(SETTINGS['target_rms']/max(level,1e-8),SETTINGS['peak_limit']/max(float(np.max(np.abs(samples))),1e-8))
        samples=np.concatenate([np.zeros(round(.18*sample_rate)),samples*gain,np.zeros(round(.35*sample_rate))])
        sf.write(raw,samples,sample_rate,subtype='PCM_16')
        encoded=TMP/f'{stem}.m4a'
        subprocess.run(['/usr/bin/afconvert','-f','m4af','-d','aac@44100','-b','96000',str(raw),str(encoded)],check=True)
        encoded.replace(audio)
        stamp.write_text(digest)
    signal,sr=sf.read(raw);duration=len(signal)/sr
    assert duration>5 and np.max(np.abs(signal))>.02,(stem,'empty or silent')
    clip_fraction=float(np.mean(np.abs(signal)>.9999));assert clip_fraction<.001,(stem,'clipping')
    rms=float(np.sqrt(np.mean(signal**2)))
    m=re.search(r'(\d+)–(\d+) min',e['title'])
    interval=(int(m[1]),int(m[2])) if m else None
    # Cover and route overview are included in the 0–10 minute preparation stage.
    row={**e,'audio':f'narration/{stem}.m4a','script':f'scripts/{stem}.txt','generation':SETTINGS,'revision':digest[:12],'duration_seconds':round(duration,2),'word_count':len(text.split()),'peak':round(float(np.max(np.abs(signal))),5),'rms':round(rms,5),'clip_fraction':clip_fraction,'stage_start_minute':interval[0] if interval else None,'stage_end_minute':interval[1] if interval else None}
    rows.append(row);print(stem,round(duration,1),'seconds',flush=True)
(OUT/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
with (OUT/'slide-audio-map.csv').open('w',newline='') as f:
    fields=['slide','title','audio','script','duration_seconds','stage_start_minute','stage_end_minute','pause_instruction']
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
for row in rows:
    if row['stage_start_minute'] is not None:
        assert row['duration_seconds']<(row['stage_end_minute']-row['stage_start_minute'])*60,(row['slide'],'narration exceeds stage')
assert sum(x['duration_seconds'] for x in rows[:3])<600,'opening exceeds preparation stage'
total=sum(x['duration_seconds'] for x in rows)
summary=f'{int(total//60)} min {round(total%60):02d} sec'
readme=f'''SESSION 2 ENGLISH NARRATION
28 audio files, numbered to match the audited 28-slide independent-study deck.
Synthetic male US English voice: Michael (Kokoro), speech speed {SPEED}.
Natural model pitch is retained; no pitch-shifting is applied. Short phrase pauses and consistent volume support clear listening.
Total spoken narration: {summary}. This is NOT the complete 180-minute lesson.
The lesson schedule includes narration, reading, pauses for calculations, Lab 08, the review test, and a ten-minute break.
Do not add three hours of narration. Pause the video/audio when instructed and resume after completing the task.

FILES
narration/slide-01.m4a through slide-28.m4a: mono AAC audio, 44.1 kHz, approximately 96 kbps.
scripts/: editable English narration text per slide.
index.html: local audio player and searchable script index. Extract the complete ZIP before opening.
slide-audio-map.csv: slide titles, audio lengths, lesson-stage times and pause cues.
manifest.json: full scripts, audio metadata and generation settings.

USE
Insert each numbered audio into its matching slide. Choose playback on click; do not automatically advance calculation or Lab slides.
Allow students to pause and replay. Audio has no background music or long silent exercise blocks.
The attendance submission route remains to be provided separately. The existing anonymous exit/feedback form does not record named attendance.

VOICE SOURCE
Kokoro-82M: https://huggingface.co/hexgrad/Kokoro-82M
Local inference: https://github.com/thewh1teagle/kokoro-onnx
Scientific spelling is retained in the visible scripts. Speech-only aliases guide the pronunciation of Antoine and Raoult.
'''
(OUT/'README.txt').write_text(readme)
sections=[]
for row in rows:
    e=html.escape
    seconds=round(row['duration_seconds']);length=f"{seconds//60}:{seconds%60:02d}"
    sections.append(f'''<section id="slide-{row['slide']:02d}" data-search="{e((row['title']+' '+row['narration']).lower(),quote=True)}"><h2>{row['slide']:02d}. {e(row['title'])}</h2><p class="meta">Audio {length} <a href="{row['audio']}" download>Download audio</a> <a href="{row['script']}" download>Download script</a></p><audio controls preload="metadata" src="{row['audio']}?v={row['revision']}"></audio><p class="cue">{e(row['pause_instruction'])}</p><details><summary>Narration script</summary><div class="script">{e(row['narration'])}</div></details></section>''')
(OUT/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Session 2 English narration</title><style>body{font:17px/1.55 system-ui,sans-serif;color:#333f4a;background:#f5f6f5;margin:0}main{max-width:850px;margin:auto;padding:28px}h1{font-size:30px}h2{font-size:21px}section{background:white;padding:20px;margin:24px 0;border-top:3px solid #0f6e6b}a{color:#0f6e6b;margin-right:16px}.meta{font-size:14px}audio{width:100%}.cue{padding:10px;border-left:4px solid #e29a2d}.script{white-space:pre-wrap}input{font:inherit;padding:10px;width:100%;box-sizing:border-box}summary{cursor:pointer}header p{max-width:75ch}</style><main><header><h1>Session 2 English narration</h1><p>28 slide-by-slide audio files. Synthetic male US English voice: Michael. Total narration: '''+summary+'''. The 180-minute lesson also includes calculations, Lab practice and a break.</p><p>A deeper male voice, with measured phrasing and consistent volume. Play each file on its matching slide. Pause to work when prompted. <a href="README.txt">Usage notes</a><a href="slide-audio-map.csv">Audio map</a></p><label for="search">Find a slide or topic</label><input id="search" type="search" placeholder="Gamma, Antoine, worksheet..."/></header>'''+''.join(sections)+'''</main><script>document.querySelector('#search').addEventListener('input',e=>document.querySelectorAll('section').forEach(s=>s.hidden=!s.dataset.search.includes(e.target.value.toLowerCase())));document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})));</script></html>''')
zip_path=OUT.parent/'week02-english-narration.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(OUT.parent))
print('TOTAL',summary,'ZIP',zip_path,flush=True)
