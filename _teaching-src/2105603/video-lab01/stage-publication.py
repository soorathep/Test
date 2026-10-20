"""Stage the verified Lab 01 supplement and reproducible sources in the existing site."""
from pathlib import Path
import argparse, hashlib, json, re, shutil
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/lab01-video'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--site',type=Path,required=True);args=p.parse_args()
course=args.site/'teaching/2105603'
assert (course/'postmidterm-01.html').is_file()
script=json.loads((SOURCE/'narration.json').read_text());manifest=json.loads((OUT/'audio/manifest.json').read_text());timeline=json.loads((OUT/'timeline.json').read_text())
assert len(script)==len(manifest)==len(timeline['slides'])==14
for a,b in zip(script,manifest):
    assert ' '.join(a['narration'].split())==b['narration']
    assert a['slide_id']==b['slide_id'] and a['activity_minutes']==b['activity_minutes']
assert sha(OUT/'audio/manifest.json')==timeline['source_manifest_sha256']
assert sha(OUT/'lab01-demo.mp4')==timeline['video_sha256']
for name in ('video-qa.json','audio/audio-qa.json'):
    report=json.loads((OUT/name).read_text());assert report['passed'] is True,name
assert json.loads((OUT/'browser-export-qa.json').read_text())['status']=='pass'
assert json.loads((OUT/'capture-review.json').read_text())['status']=='passed'
controller=json.loads((OUT/'player-controller-qa.json').read_text())
assert controller['chapters']==14 and controller['mode'].startswith('actual timing metadata')
assert all(t['status']=='passed' for t in controller['tests'])
page=(OUT/'lab01-video.html').read_text()
assert len(json.loads(re.search(r'<script id="chapter-data" type="application/json">(.*?)</script>',page,re.S)[1]))==14
assert controller['script_sha256']==hashlib.sha256(page.split('</script><script>',1)[1].split('</script>',1)[0].encode()).hexdigest()
media=course/'media/lab01';media.mkdir(parents=True,exist_ok=True)
for name in ('lab01-demo.mp4','lab01-poster.png','lab01-captions.vtt'):shutil.copy2(OUT/name,media/name)
shutil.copy2(OUT/'lab01-video.html',course/'lab01-video.html')
shutil.copy2(OUT/'browser-exports/lab01-demo-comparison.json',course/'files/lab01-demo-comparison.json')
assert (course/'files/week01-lab-guide.pdf').is_file()
archive=args.site/'_teaching-src/2105603/video-lab01';archive.mkdir(parents=True,exist_ok=True)
for name in ('README.md','requirements.txt','narration.json','narration-draft.json','build-narration.py','check-audio.py','build-video.py','build-video-page.py','test-player.mjs','prepare-scenes.py','demo-scenes.json','stage-publication.py','verify-publication.py'):
    shutil.copy2(SOURCE/name,archive/name)
frames=archive/'demo-frames';frames.mkdir(exist_ok=True)
for name in sorted({s['file'] for s in json.loads((SOURCE/'demo-scenes.json').read_text())['scenes']}):shutil.copy2(SOURCE/'demo-frames'/name,frames/name)
exports=archive/'browser-exports';exports.mkdir(exist_ok=True)
for file in (OUT/'browser-exports').iterdir():
    if file.suffix in ('.json','.csv'):shutil.copy2(file,exports/file.name)
verification=archive/'verification';verification.mkdir(exist_ok=True)
for name in ('timeline.json','video-qa.json','player-controller-qa.json','browser-export-qa.json','scientific-qa.json','capture-review.json','offline-qa.json','page-resource-qa.json','browser-qa.json'):
    file=OUT/name
    if file.exists(): (verification/name).write_text(file.read_text().replace(str(ROOT),'<workspace>').replace(str(args.site),'<website>'))
for name in ('manifest.json','audio-qa.json','spot-check-transcripts.json'):
    file=OUT/'audio'/name
    if file.exists():shutil.copy2(file,verification/name)
shutil.copy2(OUT/'scientific-check.mjs',verification/'scientific-check.mjs')
print(f'Staged 14-chapter Lab 01 supplement, guide link, comparison, media, editable sources and QA at {args.site}')
