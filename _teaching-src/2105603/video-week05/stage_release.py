"""Stage the reviewed Week 5 publication into an explicit website checkout.

Only approved public assets and compact reproducible source are copied.
Voice models, sentence caches, WAVs and private reports are not published.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(a,b):
    b.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(a,b)

parser=argparse.ArgumentParser()
parser.add_argument('--site',type=Path,required=True)
a=parser.parse_args();site=a.site.resolve()
public=site/'teaching/2105603';source=site/'_teaching-src/2105603';out=ROOT/'outputs/week05-video'
qa=read(out/'video-qa.json')
assert qa['passed'],'Video verification must pass before staging.'
assert (out/'week05-lecture.mp4').stat().st_size<100_000_000
timeline=read(out/'timeline.json');assert len(timeline['slides'])==32
contract=read(HERE/'documents/lesson-contract.json')
assert sum(x['pause_minutes'] for x in contract['slides'])==138
assert digest(out/'week05-video-slides.pdf')==timeline['source_pdf_sha256']

for name in ['week05-study.html','week05-video.html']:
    content=(HERE/'web'/name).read_text()
    assert 'production target' not in content.lower()
    assert '13 November' in content or 'November 13' in content
    copy(HERE/'web'/name,public/name)
    copy(HERE/'web'/name,source/name)
for name in ['week05-lecture.mp4','week05-poster.png','week05-captions.vtt']:
    copy(out/name,public/'media/week05'/name)
copy(out/'week05-video-slides.pdf',public/'files/postmidterm-05-slides.pdf')
for f in (HERE/'documents/output/pdf').glob('week05-*.pdf'):
    copy(f,public/'files'/f.name)
copy(HERE/'documents/postmidterm-05.qmd',source/'postmidterm-05.qmd')
copy(HERE/'documents/assets/week05-independent.css',source/'assets/week05-independent.css')
copy(HERE/'documents/assets/week05-independent.css',public/'assets/week05-independent.css')

dest=source/'video-week05'
for rel in ['README.md','export-slides.mjs','serve_preview.py','stage_release.py','update-course-links.py']:
    copy(HERE/rel,dest/rel)
for rel in ['lesson-contract.json','build_week05.py','documents-qa.json']:
    copy(HERE/'documents'/rel,dest/'documents'/rel)
for rel in ['narration.json','build-narration.py','build-video.py','qa-audio.py','qa-audio-review-decisions.json','demo-scenes.json','demo-capture-qa.json']:
    copy(HERE/'media'/rel,dest/'media'/rel)
for dirname in ['demo-frames','downloads']:
    for f in (HERE/'media'/dirname).glob('*'):
        if f.is_file():copy(f,dest/'media'/dirname/f.name)
for f in (HERE/'web').iterdir():
    if f.is_file() and f.suffix in ['.py','.js','.mjs','.css','.html','.txt','.md']:
        copy(f,dest/'web'/f.name)
for f in (HERE/'offline').iterdir():
    if f.is_file() and f.suffix in ['.py','.txt','.md']:
        copy(f,dest/'offline'/f.name)
for name in ['timeline.json','caption-timeline.json','video-qa.json']:
    copy(out/name,dest/'qa'/name)
for name in ['manifest.json','audio-qa.json']:
    copy(out/'audio'/name,dest/'qa'/('audio-'+name))
for f in (HERE/'web/qa').glob('*.json'):copy(f,dest/'qa'/f.name)
copy(out/'week05-video-slides.pdf',dest/'reviewed-slides.pdf')
print('Staged the Week 5 lesson, verified media, documents and reproducible source allowlist.')
