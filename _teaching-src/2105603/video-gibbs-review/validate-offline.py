"""Verify the offline package retains review resources and points omitted videos online.

Set SKH_WEBSITE_DIR to the staged website checkout and run after build-offline.py.
No browser playback, remote deployment or private student data is inspected.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import zipfile


VIDEO_PAGES = ('week02-video.html', 'week03-video.html', 'week04-video.html',
               'lab08-video.html', 'lab01-video.html', 'week03-gibbs-review-video.html')
PREFIX = 'thermodynamics-offline/'
BASE = 'https://www.skhgroup.net/teaching/2105603/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def offline_html(source):
    source = re.sub(r'<link\b[^>]*href=["\']https://fonts\.(?:googleapis|gstatic)\.com[^>]*>', '', source)
    source = source.replace('../files/thermodynamics-offline.zip', '/README.txt')
    for name in VIDEO_PAGES:
        pattern = r'href=(["\'])(?:\.\./|\./|/teaching/2105603/)?' + re.escape(name) + r'([?#][^"\']*)?\1'
        source = re.sub(pattern, lambda match: 'href=' + match[1] + BASE + name + (match[2] or '') + match[1], source)
    for name in ('eos', 'fugacity', 'solution', 'vle', 'stability', 'reaction'):
        source = source.replace('files/' + name + '-slides.pdf', name + '.html')
    return re.sub(r'href="(?:\./)?files/[^"\n]+\.zip"', 'href="/README.txt"', source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=Path(os.environ.get('SKH_WEBSITE_DIR', str(Path.home() / 'Documents/GitHub/Test'))))
    parser.add_argument('--output', type=Path, default=Path.home() / 'Documents/Projects/Adv thermo/outputs/gibbs-review-video/offline-qa.json')
    args = parser.parse_args()
    course = args.site / 'teaching/2105603'
    archive = course / 'files/thermodynamics-offline.zip'
    assert archive.stat().st_size < 100_000_000
    results = []
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        names = package.namelist()
        assert len(names) == len(set(names)), 'Duplicate archive entries.'
        assert all(n.startswith(PREFIX) and '..' not in PurePosixPath(n).parts for n in names)
        excluded = [n for n in names if '/media/' in n or Path(n).suffix.lower() in ('.mp4', '.m4a', '.wav', '.mp3', '.aac', '.webm', '.mov', '.ogg')
                    or any(part in ('.git', '.env', '.DS_Store', '__MACOSX', 'reports', '__pycache__') for part in PurePosixPath(n).parts)]
        assert not excluded, excluded
        for name in VIDEO_PAGES:
            assert PREFIX + 'teaching/2105603/' + name not in names
        manifest = json.loads(package.read(PREFIX + 'MANIFEST.json'))
        assert set(names) == {PREFIX + name for name in manifest} | {PREFIX + 'MANIFEST.json'}
        for name, digest in manifest.items():
            assert sha(package.read(PREFIX + name)) == digest, name
        import pymupdf
        for name, count in (('week03-gibbs-review-slides.pdf', 26), ('week03-gibbs-review-guide.pdf', 4)):
            rel = 'teaching/2105603/files/' + name
            data = package.read(PREFIX + rel)
            assert data == (course / 'files' / name).read_bytes()
            assert len(pymupdf.open(stream=data, filetype='pdf')) == count
            results.append({'file': rel, 'pages': count, 'sha256': sha(data), 'byte_identical_to_public': True})
        for name in ('week03-gibbs-review.html', 'week03-study.html'):
            rel = 'teaching/2105603/' + name
            text = package.read(PREFIX + rel).decode()
            assert text == offline_html((course / name).read_text())
            results.append({'file': rel, 'matches_public_after_documented_link_rewrites': True})
        example = 'teaching/2105603/files/gibbs-review-lab04-study.json'
        data = package.read(PREFIX + example)
        assert data == (args.site / example).read_bytes()
        study = json.loads(data)
        assert study['workspace']['lab'] == 'stability' and study['workspace']['context']['fitKind'] == 'synthetic'
        assert study['result']['A'] == 3 and study['result']['z'] == .35
        results.append({'file': example, 'sha256': sha(data), 'synthetic_demonstration_only': True})
        for figure in ('curve', 'gap', 'regions', 'tpd'):
            rel = f'teaching/2105603/figures/gibbs-review-{figure}.svg'
            assert package.read(PREFIX + rel) == (args.site / rel).read_bytes()
        wrong_links = []
        for name in names:
            if not name.endswith('.html'):
                continue
            for href in re.findall(r'href=["\']([^"\']+)["\']', package.read(name).decode()):
                if any(v in href for v in VIDEO_PAGES) and not href.startswith(BASE):
                    wrong_links.append({'file': name, 'href': href})
        assert not wrong_links, wrong_links
        for name in ('index.html', 'README.txt'):
            text = package.read(PREFIX + name).decode()
            assert BASE + 'week03-gibbs-review-video.html' in text
        route = package.read(PREFIX + 'teaching/2105603/week03-study.html').decode()
        assert BASE + 'week03-gibbs-review-video.html' in route
        rel = 'teaching/2105603/labs/stability.html'
        assert package.read(PREFIX + rel).decode() == offline_html((args.site / rel).read_text())
        rel = 'teaching/2105603/labs/release-manifest.json'
        assert package.read(PREFIX + rel) == (args.site / rel).read_bytes()
    report = {'status': 'pass', 'scope': 'Offline integrity and Gibbs review resources; no playback or deployment claim.',
              'archive': 'teaching/2105603/files/thermodynamics-offline.zip', 'archive_sha256': sha(archive.read_bytes()),
              'archive_bytes': archive.stat().st_size, 'manifest_files_verified': len(manifest), 'files': results,
              'omitted_video_pages': list(VIDEO_PAGES), 'relative_omitted_player_links': wrong_links,
              'private_or_media_files': excluded}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': 'pass', 'manifest_files_verified': len(manifest), 'archive_MB': round(archive.stat().st_size / 1e6, 2)}))


if __name__ == '__main__':
    main()
