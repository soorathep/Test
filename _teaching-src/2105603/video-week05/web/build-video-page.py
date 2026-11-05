"""Build the Week 5 study route and video player from the shared lesson contract.

The published video page requires a final SHA-256-bearing media timeline. Use
--study-only before encoding; its recording duration is explicitly a target.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import math
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CONTRACT=HERE.parent/'documents/lesson-contract.json'

def read(path):return json.loads(path.read_text())
def esc(value):return html.escape(str(value),quote=True)
def clock(seconds):
    seconds=int(round(seconds));return f'{seconds//60}:{seconds%60:02d}'
def rows_of(value):
    if isinstance(value,list):return value
    for key in ('slides','chapters','timeline'):
        if isinstance(value.get(key),list):return value[key]
    raise ValueError('Expected an array or a slides/chapters/timeline array.')
def validate_contract(c):
    assert c['week']==5 and c['slide_count']==32 and len(c['slides'])==32
    assert [s['number'] for s in c['slides']]==list(range(1,33))
    assert len({s['id'] for s in c['slides']})==32
    assert sum(s['pause_minutes'] for s in c['slides'] if s['id']!='break')==c['work_minutes']==128
    assert sum(s['pause_minutes'] for s in c['slides'] if s['id']=='break')==c['break_minutes']==10
    assert c['date']=='2026-11-06' and c['next_in_person_class']=='2026-11-13'
    return c

def prepare_rows(contract,manifest,timeline):
    assert len(manifest)==len(timeline)==32,'Narration and timeline must contain 32 slides.'
    rows=[]
    for c,m,t in zip(contract['slides'],manifest,timeline):
        n=c['number'];expected=c['pause_minutes']
        for s in (m,t):
            assert s.get('slide')==n,f'Slide {n}: ordering mismatch.'
            if s.get('slide_id'):assert s['slide_id']==c['id'],f'Slide {n}: chapter identity mismatch.'
        assert m.get('title')==c['title'],f'Slide {n}: title differs from contract.'
        assert isinstance(m.get('narration'),str) and m['narration'].strip()
        assert m.get('activity') is (expected>0),f'Slide {n}: narration activity flag mismatch.'
        assert float(m.get('activity_minutes',0))==expected,f'Slide {n}: narration time budget mismatch.'
        if 'activity' in t:assert t['activity'] is (expected>0)
        if 'activity_minutes' in t:assert float(t['activity_minutes'])==expected
        start=float(t.get('start_seconds',t.get('start',-1)));end=float(t.get('end_seconds',t.get('end',-1)))
        assert math.isfinite(start+end) and start>=0 and end-start>.3,'Invalid video time boundary.'
        assert abs(start-(rows[-1]['end'] if rows else 0))<.012,'Timeline is not contiguous.'
        assert float(t.get('narration_end_seconds',end-.25))<=end-.24+1e-6,'Activity guard would interrupt narration.'
        cue=m.get('pause_instruction') or m.get('activity_instruction') or ''
        if expected:assert cue.strip(),f'Slide {n}: missing activity instruction.'
        else:cue=cue or f"Follow slide {n}; keep worksheet {c['worksheet']} beside you. Attempt questions before their checks."
        rows.append(dict(slide=n,slide_id=c['id'],anchor=f'slide-{n}',title=m['title'],narration=m['narration'],cue=cue,worksheet=c['worksheet'],activity=expected>0,activity_minutes=expected,is_break=c['id']=='break',is_demo=n in (20,22,30),start=start,end=end))
    return rows

def style():return (HERE/'player.css').read_text()
def fill(template,values):
    for key,value in values.items():template=template.replace('@@'+key+'@@',str(value))
    assert '@@' not in template,'Unresolved HTML placeholder.'
    return template

def study_html(c,recording_seconds=None):
    validate_contract(c)
    if recording_seconds is None:
        timing=f"The production target is <strong>{c['narration_target_minutes']} minutes of recording</strong>, plus <strong>128 minutes of work</strong> and a <strong>10-minute break</strong>: 180 minutes planned. The published video page will show the measured recording duration."
    else:
        total=recording_seconds/60+c['work_minutes']+c['break_minutes']
        timing=f"The recording is <strong>{clock(recording_seconds)}</strong>. Add <strong>128 minutes of worksheet, Lab and reflection work</strong> and a <strong>10-minute break</strong>: approximately <strong>{total:.1f} minutes</strong> in total. These are planning budgets, not measured student completion times."
    blocks=[
      ('1–4','R1–R2 · Review Week 4','8','Worksheet p. 1. Distinguish partial and total pressure. Check the gas equation and Langmuir equation independently before checking the total balance. Pause at slides 2 and 3; check at slide 4.'),
      ('5–9','A1–A3 · Build the reaction quotient','10','Worksheet p. 2. Write amounts, mole fractions and Q for A₂ ⇌ 2A. Pause at slide 8 before viewing slide 9.'),
      ('10–14','B1–B4 · Direction and two routes to K','16','Worksheet pp. 2–3. Use the natural logarithm and consistent energy units. Pause at slide 10 and slide 13. Check at slide 14.'),
      ('15–18','C1–C4 · Solve reference and pressure cases','23','Worksheet pp. 3–4. Calculate extent, amounts, fractions, atom balance and Q. Pause at slides 15 and 17 before their checks.'),
      ('19–22','D1–D4 · Lab 12 reference and pressure','27','Worksheet p. 4; Lab guide p. 1. Prepare inputs for 5 minutes at slide 19. Watch the actual Lab demonstration at slide 20. Run 12A and 12B for 22 minutes at slide 21, then check the results at slide 22.'),
      ('23','Break','10','Save your worksheet and exported cases. Take a ten-minute break. This is included in the lesson budget.'),
      ('24–28','E1–E3 · Temperature and van’t Hoff','15','Worksheet p. 5. Use constant ΔH° to calculate K at 400 K and then equilibrium extent at 100 kPa. Pause at slide 26, check at slide 27, and read the model limits at slide 28.'),
      ('29–30','F1–F3 · Temperature case and JSON restore','19','Worksheet p. 5; Lab guide p. 2. Run 12C at 400 K and 100 kPa using constant-ΔH° van’t Hoff. Export it, then restore 12A and verify the recalculated inputs and results. Pause at slide 29; use slide 30 to check.'),
      ('31–32','G · Exit ticket and feedback','10','Worksheet p. 6. Bring one unresolved question to the 13 November class. Submit the existing Session 5 form once, wait for “Response received,” and keep your files.')]
    body=''.join(f'<tr role="row"><td role="cell" headers="schedule-video"><a href="week05-video.html#slide-{a.split("–")[0]}">Slides {a}</a></td><td role="cell" headers="schedule-section"><strong>{esc(b)}</strong></td><td role="cell" headers="schedule-minutes">{mins}</td><td role="cell" headers="schedule-instructions">{esc(d)}</td></tr>' for a,b,mins,d in blocks)
    return fill((HERE/'study-template.html').read_text(),{'STYLE':style(),'TIMING':timing,'SCHEDULE':body,'EXIT_URL':esc(c['exit_url'])})

def build(contract_path,manifest_path,timeline_path,output_path,study_output):
    c=validate_contract(read(contract_path));manifest=rows_of(read(manifest_path));raw=read(timeline_path)
    assert isinstance(raw,dict),'Production timeline needs final media provenance.'
    digest=raw.get('video_sha256')
    assert isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest),'Final encoded video_sha256 is required.'
    rows=prepare_rows(c,manifest,rows_of(raw));version=digest[:12];duration=rows[-1]['end'];total=duration/60+138
    chapters=[];transcripts=[]
    for r in rows:
        badge=('<span class="activity-dot">Break</span>' if r['is_break'] else f'<span class="activity-dot">Work {r["activity_minutes"]} min</span>' if r['activity'] else '')
        if r['is_demo']:badge+='<span class="activity-dot">Lab 12 screen demo</span>'
        chapters.append(f'<li><a class="chapter" href="#{r["anchor"]}" data-slide="{r["slide"]}"><span class="chapter-number">{r["slide"]:02d}</span><span class="chapter-copy">{esc(r["title"])}<span class="chapter-meta"><time>{clock(r["start"])}</time>{badge}</span></span></a></li>')
        transcripts.append(f'<section aria-labelledby="transcript-{r["slide"]}"><h3 id="transcript-{r["slide"]}">Slide {r["slide"]}: {esc(r["title"])}</h3><p class="control-note">Recording {clock(r["start"])} · Worksheet {esc(r["worksheet"])}</p><p class="transcript-copy">{esc(r["narration"])}</p><p class="cue"><strong>Your action:</strong> {esc(r["cue"])}</p></section>')
    data=json.dumps(rows,ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')
    values={'STYLE':style(),'SCRIPT':(HERE/'player.js').read_text(),'DATA':data,'VERSION':version,'DURATION':clock(duration),'RECORDING_MINUTES':f'{duration/60:.1f}','TOTAL_MINUTES':f'{total:.1f}','CHAPTERS':'\n'.join(chapters),'TRANSCRIPTS':'\n'.join(transcripts),'FIRST_TITLE':esc(rows[0]['title']),'FIRST_NARRATION':esc(rows[0]['narration']),'FIRST_CUE':esc(rows[0]['cue']),'WORK_STOPS':sum(r['activity'] and not r['is_break'] for r in rows),'EXIT_URL':esc(c['exit_url'])}
    page=fill((HERE/'video-template.html').read_text(),values)
    for asset in ('week05-lecture.mp4','week05-captions.vtt','week05-poster.png'):
        path='./media/week05/'+asset;page=page.replace(path,path+'?v='+version)
    output_path.parent.mkdir(parents=True,exist_ok=True);output_path.write_text(page)
    study_output.parent.mkdir(parents=True,exist_ok=True);study_output.write_text(study_html(c,duration))
    qa={'slides':len(rows),'work_minutes':128,'break_minutes':10,'recording_seconds':duration,'total_minutes':total,'video_sha256':digest,'contract_sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest(),'pause_slides':[r['slide'] for r in rows if r['activity']],'demo_slides':[r['slide'] for r in rows if r['is_demo']]}
    (output_path.parent/'week05-page-build-qa.json').write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps(qa,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',type=Path,default=CONTRACT);p.add_argument('--manifest',type=Path,default=ROOT/'outputs/week05-video/audio/manifest.json');p.add_argument('--timeline',type=Path,default=ROOT/'outputs/week05-video/timeline.json');p.add_argument('--output',type=Path,default=HERE/'week05-video.html');p.add_argument('--study-output',type=Path,default=HERE/'week05-study.html');p.add_argument('--study-only',action='store_true');a=p.parse_args()
    if a.study_only:a.study_output.write_text(study_html(validate_contract(read(a.contract))));print('Built study route with recording target, pending measured timing.')
    else:build(a.contract,a.manifest,a.timeline,a.output,a.study_output)
