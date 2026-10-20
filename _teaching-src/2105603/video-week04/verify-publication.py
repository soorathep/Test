"""Verify public Week 4 resources against the staged release, without submitting forms."""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.skhgroup.net/teaching/2105603/'
FILES = [
    'week04-video.html', 'week04-study.html', 'postmidterm-04.html',
    'files/postmidterm-04-slides.pdf', 'files/week04-practice.pdf',
    'files/week04-lab-guide.pdf', 'files/week04-solutions.pdf',
    'files/preclass-week-04.pdf', 'media/week04/week04-captions.vtt',
    'media/week04/week04-poster.png', 'files/thermodynamics-offline.zip',
    'labs/release-manifest.json',
]

def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, required=True)
    args = parser.parse_args()
    course = args.site / 'teaching/2105603'

    def verify(name):
        request = urllib.request.Request(BASE + name, headers={'Accept-Encoding': 'identity'})
        with urllib.request.urlopen(request, timeout=90) as response:
            body = response.read()
            assert response.status == 200, (name, response.status)
            content_type = response.headers.get('Content-Type')
        local = (course / name).read_bytes()
        assert sha(body) == sha(local), f'Published content differs: {name}'
        return {'path': name, 'status': 200, 'bytes': len(body),
                'sha256': sha(body), 'content_type': content_type}

    with ThreadPoolExecutor(max_workers=4) as pool:
        verified = list(pool.map(verify, FILES))
    name = 'media/week04/week04-lecture.mp4'
    path = course / name
    size = path.stat().st_size
    ranges = []
    for start, end in [(0, 255), (size-256, size-1)]:
        request = urllib.request.Request(BASE+name, headers={
            'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'})
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            assert response.status == 206, response.status
            assert response.headers.get('Content-Range') == f'bytes {start}-{end}/{size}'
            content_type = response.headers.get('Content-Type')
            assert content_type.startswith('video/mp4'), content_type
        with path.open('rb') as source:
            source.seek(start)
            assert body == source.read(end-start+1)
        ranges.append({'start': start, 'end': end, 'status': 206,
                       'matching_local_bytes': True})
    report = {'passed': True, 'verified_files': verified,
              'video': {'path': name, 'size_bytes': size, 'ranges': ranges},
              'note': 'File hashes and first/last MP4 byte ranges verified; browser playback is checked separately. No student response submitted.'}
    output = ROOT / 'outputs/week04-video/publication-qa.json'
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': True, 'files': len(verified), 'video_bytes': size,
                      'range_checks': len(ranges)}, indent=2))

if __name__ == '__main__':
    main()
