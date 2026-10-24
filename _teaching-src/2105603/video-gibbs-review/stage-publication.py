"""Stage verified Gibbs review media and teaching sources in an existing website.

This only copies reviewed outputs. It never commits, pushes or deploys.
Run after the final recording, player checks and human review are complete.
The allowlists exclude model weights, PCM caches, reports and student data.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import shutil


DEFAULT_WORKSPACE = Path.home() / 'Documents/Projects/Adv thermo'
SOURCE_FILES = (
    'README-build.md', 'README-publication.md', 'prepare-narration.py',
    'build-narration.py', 'build-video.py', 'build-video-page.py',
    'test-player.mjs', 'stage-publication.py', 'build-offline.py',
    'validate-offline.py', 'narration-draft.json', 'narration.json',
    'narration-scientific-qa.json', 'demo-scenes.json', 'demo-ui-verification.json',
    'gibbs-review-lab04-study.json',
)
MEDIA_FILES = (
    'gibbs-review.mp4', 'gibbs-review-poster.png',
    'gibbs-review-captions.vtt', 'gibbs-review-transcript.txt',
)
REQUIRED_EVIDENCE = ('timeline.json', 'timeline.csv', 'manifest.json',
                     'caption-timeline.json', 'video-qa.json', 'player-controller-qa.json')
OPTIONAL_EVIDENCE = ('browser-qa.json', 'page-resource-qa.json', 'offline-qa.json',
                     'content-qa.json', 'publication-qa.json')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument('--check-only', action='store_true', help='Validate the staging inputs without copying anything.')
    args = parser.parse_args()
    workspace, site = args.workspace.resolve(), args.site.resolve()
    source, output = workspace / 'asynchronous-gibbs-review', workspace / 'outputs/gibbs-review-video'
    course = site / 'teaching/2105603'
    require((course / 'week03-gibbs-review.html').is_file(), 'Choose the existing website checkout with the review deck.')
    required = [(source / name) for name in SOURCE_FILES]
    required += [(output / name) for name in (*MEDIA_FILES, *REQUIRED_EVIDENCE, 'week03-gibbs-review-video.html')]
    required += [output / 'audio/manifest.json', output / 'audio/audio-qa.json', output / 'audio/spot-check-transcripts.json']
    for path in required:
        require(path.is_file() and not path.is_symlink(), f'Missing or unsafe staging input: {path.relative_to(workspace)}')
    timeline = json.loads((output / 'timeline.json').read_text())
    manifest = json.loads((output / 'manifest.json').read_text())
    audio_manifest = json.loads((output / 'audio/manifest.json').read_text())
    narration = json.loads((source / 'narration.json').read_text())
    video_qa = json.loads((output / 'video-qa.json').read_text())
    audio_qa = json.loads((output / 'audio/audio-qa.json').read_text())
    asr = json.loads((output / 'audio/spot-check-transcripts.json').read_text())
    controller = json.loads((output / 'player-controller-qa.json').read_text())
    for rows in (manifest, audio_manifest, narration, timeline['slides']):
        require(len(rows) == 26 and [r['slide'] for r in rows] == list(range(1, 27)), 'Rebuild the 26-chapter recording before staging.')
    for original, rendered, spoken in zip(narration, manifest, audio_manifest):
        for key in ('narration', 'title', 'slide_id', 'activity', 'activity_minutes', 'pause_instruction'):
            require(original[key] == rendered[key] == spoken[key], f'Narration metadata changed after synthesis: slide {original["slide"]}, {key}')
    require(sum(r['activity_minutes'] for r in manifest) == 29, 'The optional activity budget must remain 29 minutes.')
    require(sha(output / 'audio/manifest.json') == timeline['source_manifest_sha256'], 'Audio manifest hash differs from the final timeline.')
    require(sha(output / 'gibbs-review.mp4') == timeline['video_sha256'], 'Video hash differs from the final timeline.')
    require(0 < (output / 'gibbs-review.mp4').stat().st_size < 100_000_000, 'MP4 exceeds the repository file-size limit.')
    require(sha(course / 'files/week03-gibbs-review-slides.pdf') == timeline['source_pdf_sha256'], 'The public PDF differs from the narrated slides.')
    require(video_qa['passed'] and video_qa['chapter_count'] == 26, 'Video QA must pass for all 26 chapters.')
    require(video_qa['video_sha256'] == timeline['video_sha256'], 'Video QA is stale.')
    require(abs(video_qa['duration_seconds'] - timeline['duration_seconds']) < .001, 'Video duration evidence disagrees.')
    require(audio_qa['passed'] and audio_qa['chapter_count'] == 26, 'Audio QA must pass for all 26 chapters.')
    require(abs(audio_qa['duration_seconds'] - sum(row['duration_seconds'] for row in audio_manifest)) < .001, 'Audio duration evidence disagrees.')
    require(audio_qa['clipped_samples'] == 0, 'Audio clipping check failed.')
    require(asr['all_26_script_and_wav_hashes_verified'] and asr['status'] == 'reviewed_no_confirmed_content_error', 'ASR spot-check review is incomplete.')
    require(asr['manifest_sha256'] == sha(output / 'audio/manifest.json'), 'ASR spot-check manifest hash is stale.')
    require(controller['chapters'] == 26 and controller['mode'].startswith('Final measured timeline'), 'Run the controller tests against final timing, without --fixture.')
    require(controller['tests'] and all(t['status'] == 'passed' for t in controller['tests']), 'Player controller tests failed.')
    require(controller['manifest_sha256'] == sha(output / 'manifest.json'), 'Player manifest QA is stale.')
    require(controller['timeline_sha256'] == sha(output / 'timeline.json'), 'Player timeline QA is stale.')
    page = (output / 'week03-gibbs-review-video.html').read_text()
    match = re.search(r'<script id="chapter-data" type="application/json">(.*?)</script><script>(.*?)</script>', page, re.S)
    require(match is not None, 'Rebuild the video page with the final chapter metadata.')
    chapters = json.loads(match[1])
    require(hashlib.sha256(match[2].encode()).hexdigest() == controller['script_sha256'], 'Page controller differs from the tested script.')
    require(len(chapters) == 26, 'The player must include 26 chapters.')
    for row, expected in zip(chapters, timeline['slides']):
        require(row['slide'] == expected['slide'] and row['title'] == expected['title'], 'Player chapters differ from final media.')
        require(abs(row['start'] - expected['start_seconds']) < .001 and abs(row['end'] - expected['end_seconds']) < .001, 'Player chapter boundaries are stale.')
    require('files/gibbs-review-lab04-study.json' in page, 'The reviewed synthetic example download is missing.')
    demo = json.loads((source / 'demo-scenes.json').read_text())['scenes']
    frames = set()
    for scene in demo:
        if scene.get('kind') == 'slide':
            continue
        capture = (workspace / scene['image']).resolve()
        require(capture.is_relative_to((source / 'demo-frames').resolve()) and capture.is_file() and not capture.is_symlink(), 'Use genuine, local reviewed Lab capture files.')
        require(capture.suffix.lower() == '.png', 'Only reviewed PNG captures are staged.')
        frames.add(capture)
    require(frames, 'No Lab captures found.')
    for row in timeline['slides']:
        for scene in row['visual_scenes']:
            if scene['kind'] == 'actual_lab_capture':
                capture = (workspace / scene['capture_source']).resolve()
                require(capture in frames and sha(capture) == scene['capture_sha256'], 'A captured Lab frame changed after encoding.')
    study = json.loads((source / 'gibbs-review-lab04-study.json').read_text())
    require(study['workspace']['lab'] == 'stability' and study['workspace']['context']['fitKind'] == 'synthetic', 'Only the reviewed synthetic Lab 04 example can be staged.')
    require(study['result']['A'] == 3 and math.isclose(study['result']['z'], .35), 'The example must match the demonstrated A = 3, z = 0.35 case.')
    if args.check_only:
        print('Staging preflight passed. No files copied.')
        return
    media = course / 'media/gibbs-review'
    archive = site / '_teaching-src/2105603/video-gibbs-review'
    verification = archive / 'verification'
    for directory in (media, archive, archive / 'demo-frames', verification):
        directory.mkdir(parents=True, exist_ok=True)
    for name in MEDIA_FILES:
        shutil.copy2(output / name, media / name)
    shutil.copy2(output / 'week03-gibbs-review-video.html', course / 'week03-gibbs-review-video.html')
    shutil.copy2(source / 'gibbs-review-lab04-study.json', course / 'files/gibbs-review-lab04-study.json')
    for name in SOURCE_FILES:
        shutil.copy2(source / name, archive / name)
    for capture in sorted(frames):
        shutil.copy2(capture, archive / 'demo-frames' / capture.name)
    def save_evidence(path, name):
        # Persist the facts and hashes while removing local account-specific paths.
        text = path.read_text().replace(str(workspace), '<workspace>').replace(str(site), '<website>')
        (verification / name).write_text(text)
    for name in REQUIRED_EVIDENCE:
        save_evidence(output / name, name)
    for name in OPTIONAL_EVIDENCE:
        if (output / name).is_file():
            save_evidence(output / name, name)
    save_evidence(output / 'audio/manifest.json', 'audio-manifest.json')
    save_evidence(output / 'audio/audio-qa.json', 'audio-qa.json')
    save_evidence(output / 'audio/spot-check-transcripts.json', 'asr-spot-check-transcripts.json')
    print(f'Staged 26-slide Gibbs review, {len(frames)} actual Lab captures, synthetic example JSON, captions, transcript and reproducible sources in {site}. No commit or deployment performed.')


if __name__ == '__main__':
    main()
