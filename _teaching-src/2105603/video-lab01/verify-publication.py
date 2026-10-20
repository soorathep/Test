"""Verify public Lab 01 resources against the staged release, without submitting forms."""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.skhgroup.net/teaching/2105603/'
FILES = [
    'lab01-video.html', 'files/week01-lab-guide.pdf',
    'files/lab01-demo-comparison.json', 'media/lab01/lab01-captions.vtt',
    'media/lab01/lab01-poster.png', 'labs/index.html', 'labs/learning-path.html',
    'labs/assets/learning-guide.js', 'labs/assets/learning-path.json',
    'labs/release-manifest.json', 'files/thermodynamics-offline.zip',
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
    request = urllib.request.Request(BASE, headers={'Accept-Encoding': 'identity'})
    with urllib.request.urlopen(request, timeout=60) as response:
        course_index=response.read().decode()
        assert response.status==200
    assert '/teaching/2105603/lab01-video.html' in course_index
    assert '/teaching/2105603/files/week01-lab-guide.pdf' in course_index
    assert 'No repeat exit-ticket or attendance submission is required.' in course_index
    index_check={'status':200,'rendered_Jekyll_index_links_present':True}
    name = 'media/lab01/lab01-demo.mp4'
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
    report = {'passed': True, 'verified_files': verified, 'course_index':index_check,
              'video': {'path': name, 'size_bytes': size, 'ranges': ranges},
              'note': 'File hashes and first/last MP4 byte ranges verified; browser playback is checked separately. No student response submitted.'}
    output = ROOT / 'outputs/lab01-video/publication-qa.json'
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': True, 'files': len(verified), 'video_bytes': size,
                      'range_checks': len(ranges)}, indent=2))

if __name__ == '__main__':
    main()
