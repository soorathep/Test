"""Copy verified Week 3 media and reproducible sources to an existing website.

This only stages files. It does not commit, push or deploy the website.
"""
from pathlib import Path
import argparse
import hashlib
import json
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
assert json.loads((OUT / 'video-qa.json').read_text())['passed']
assert json.loads((OUT / 'audio/audio-qa.json').read_text())['passed']
assert hashlib.sha256((OUT / 'week03-lecture.mp4').read_bytes()).hexdigest() == timeline['video_sha256']
assert hashlib.sha256((course / 'files/postmidterm-03-slides.pdf').read_bytes()).hexdigest() == timeline['source_pdf_sha256']
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
    'test-player.mjs', 'stage-publication.py',
):
    shutil.copy2(SOURCE / name, archive / name)
verification = archive / 'verification'
verification.mkdir(exist_ok=True)
for name in ('timeline.json', 'video-qa.json', 'study-time-qa.json', 'player-controller-qa.json'):
    shutil.copy2(OUT / name, verification / name)
for name in ('offline-qa.json', 'page-resource-qa.json', 'browser-qa.json'):
    if (OUT / name).is_file():
        shutil.copy2(OUT / name, verification / name)
for name in ('manifest.json', 'audio-qa.json'):
    shutil.copy2(OUT / 'audio' / name, verification / name)
if (OUT / 'audio/spot-check-transcripts.json').is_file():
    shutil.copy2(OUT / 'audio/spot-check-transcripts.json', verification / 'asr-spot-checks.json')
print(f'Staged 31-slide video, captions, poster, page and reproducible source in {args.site}.')
