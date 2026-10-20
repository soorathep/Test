"""Copy verified Week 3 media and reproducible sources to an existing website.

This only stages files. It does not commit, push or deploy the website.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).resolve().parent
OUT = ROOT / 'outputs/week03-video'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--site', type=Path, required=True)
args = parser.parse_args()
course = args.site / 'teaching/2105603'
assert (course / 'week03-study.html').is_file(), 'Use the existing course website checkout.'
timeline = json.loads((OUT / 'timeline.json').read_text())
manifest = json.loads((OUT / 'audio/manifest.json').read_text())
narration = json.loads((SOURCE / 'narration.json').read_text())
count = len(narration)
assert count == 44, 'Prepare the revised 44-slide source before staging.'
assert len(manifest) == len(timeline['slides']) == count, 'Stale or mismatched media metadata.'
assert [r['slide'] for r in manifest] == list(range(1, count + 1))
assert [r['slide'] for r in timeline['slides']] == list(range(1, count + 1))
for source, rendered in zip(narration, manifest):
    assert source['narration'] == rendered['narration'], 'Narration source changed after synthesis.'
    assert source['slide_id'] == rendered['slide_id']
    assert source['activity_minutes'] == rendered['activity_minutes']
assert hashlib.sha256((OUT / 'audio/manifest.json').read_bytes()).hexdigest() == timeline['source_manifest_sha256']
controller = json.loads((OUT / 'player-controller-qa.json').read_text())
assert controller['chapters'] == count and controller['mode'].startswith('actual timing metadata')
assert controller['tests'] and all(t['status'] == 'passed' for t in controller['tests'])
page = (OUT / 'week03-video.html').read_text()
chapter_data = re.search(r'<script id="chapter-data" type="application/json">(.*?)</script>', page, re.S)
assert chapter_data and len(json.loads(chapter_data[1])) == count, 'Rebuild the revised video page.'
assert controller['script_sha256'] == hashlib.sha256(page.split('</script><script>',1)[1].split('</script>',1)[0].encode()).hexdigest(), 'Controller QA is stale.'
video_qa = json.loads((OUT / 'video-qa.json').read_text())
audio_qa = json.loads((OUT / 'audio/audio-qa.json').read_text())
assert video_qa['passed'] and video_qa['chapter_count'] == count
assert video_qa['video_sha256'] == timeline['video_sha256'], 'Video QA is stale.'
assert abs(video_qa['duration_seconds'] - timeline['duration_seconds']) < .001
assert audio_qa['passed'] and audio_qa['chapter_count'] == count
assert abs(audio_qa['duration_seconds'] - sum(row['duration_seconds'] for row in manifest)) < .001
assert hashlib.sha256((OUT / 'week03-lecture.mp4').read_bytes()).hexdigest() == timeline['video_sha256']
assert hashlib.sha256((course / 'files/postmidterm-03-slides.pdf').read_bytes()).hexdigest() == timeline['source_pdf_sha256']
demo = json.loads((SOURCE / 'demo-scenes.json').read_text())
for scene in demo['scenes']:
    assert 1 <= scene['slide'] <= count
    assert Path(scene['file']).name == scene['file'], 'Demo frame paths must be local filenames.'
    assert (SOURCE / 'demo-frames' / scene['file']).is_file()
media = course / 'media/week03'
media.mkdir(parents=True, exist_ok=True)
for name in ('week03-lecture.mp4', 'week03-poster.png', 'week03-captions.vtt'):
    shutil.copy2(OUT / name, media / name)
shutil.copy2(OUT / 'week03-video.html', course / 'week03-video.html')
archive = args.site / '_teaching-src/2105603/video-week03'
archive.mkdir(parents=True, exist_ok=True)
for name in (
    'README.md', 'requirements.txt', 'lesson-contract.txt', 'narration-draft.json',
    'narration.json', 'prepare-narration.py', 'build-narration.py',
    'calibrate-activities.py', 'build-video.py', 'build-video-page.py',
    'test-player.mjs', 'stage-publication.py', 'demo-scenes.json',
):
    shutil.copy2(SOURCE / name, archive / name)
for name in ('narration-theory-draft.json', 'narration-demo-draft.json', 'narration-lle-draft.json', 'revised-deck-text.json'):
    if (SOURCE / name).is_file():
        shutil.copy2(SOURCE / name, archive / name)
frames = archive / 'demo-frames'
frames.mkdir(exist_ok=True)
for frame in sorted((SOURCE / 'demo-frames').glob('*.png')):
    assert not frame.is_symlink(), 'Archive real reviewed demo images, not symlinks.'
    shutil.copy2(frame, frames / frame.name)
verification = archive / 'verification'
verification.mkdir(exist_ok=True)
for name in ('timeline.json', 'video-qa.json', 'study-time-qa.json', 'player-controller-qa.json'):
    shutil.copy2(OUT / name, verification / name)
for name in ('offline-qa.json', 'page-resource-qa.json', 'browser-qa.json', 'content-qa.json'):
    if (OUT / name).is_file():
        shutil.copy2(OUT / name, verification / name)
for name in ('manifest.json', 'audio-qa.json'):
    shutil.copy2(OUT / 'audio' / name, verification / name)
if (OUT / 'audio/spot-check-transcripts.json').is_file():
    shutil.copy2(OUT / 'audio/spot-check-transcripts.json', verification / 'asr-spot-checks.json')
print(f'Staged {count}-slide video, actual Lab 03 and Lab 04 demo frames, captions, poster, page and reproducible source in {args.site}.')
