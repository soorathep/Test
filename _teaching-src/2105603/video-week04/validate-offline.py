"""Verify the final Week 4 offline archive against the staged public course.

Run with the absolute research interpreter after tools/build-offline.py.
Set SKH_WEBSITE_DIR to the public website checkout. The JSON report uses
repository-relative paths and contains no machine-specific paths.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SITE = Path(os.environ.get("SKH_WEBSITE_DIR", str(Path.home() / "Documents/GitHub/Test")))
COURSE = SITE / "teaching/2105603"
PREFIX = "thermodynamics-offline/"
PDFS = {
    "postmidterm-04-slides.pdf": 40,
    "preclass-week-04.pdf": 3,
    "week04-practice.pdf": 6,
    "week04-lab-guide.pdf": 4,
    "week04-solutions.pdf": 4,
}
HTML = ("week04-study.html", "postmidterm-04.html", "postmidterm-04-appendix.html")
VIDEO_PAGES = ("week02-video.html", "week03-video.html", "week04-video.html", "lab08-video.html")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def permitted_html_rewrites(source):
    """The archive deliberately changes online-only and omitted-file links."""
    source = re.sub(r'<link\b[^>]*href=["\']https://fonts\.(?:googleapis|gstatic)\.com[^>]*>', '', source)
    source = source.replace('../files/thermodynamics-offline.zip', '/README.txt')
    for name in VIDEO_PAGES:
        pattern = r'href=(["\'])(?:\.\./|\./|/teaching/2105603/)?' + re.escape(name) + r'([?#][^"\']*)?\1'
        source = re.sub(pattern, lambda m: 'href=' + m[1] +
                        'https://www.skhgroup.net/teaching/2105603/' + name +
                        (m[2] or '') + m[1], source)
    for name in ('eos', 'fugacity', 'solution', 'vle', 'stability', 'reaction'):
        source = source.replace('files/' + name + '-slides.pdf', name + '.html')
    return re.sub(r'href="(?:\./)?files/[^"\n]+\.zip"', 'href="/README.txt"', source)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/week04-video/offline-qa.json')
    args = parser.parse_args()
    archive = COURSE / 'files/thermodynamics-offline.zip'
    # A finished live player must exist before we accept the offline edition.
    player = (COURSE / 'week04-video.html').read_text()
    chapters_match = re.search(r'<script\b[^>]*id="chapter-data"[^>]*>(.*?)</script>', player, re.S)
    assert chapters_match, 'Staged Week 4 player is missing its chapter data.'
    chapters = json.loads(chapters_match[1])
    assert len(chapters) == 40 and [c['slide'] for c in chapters] == list(range(1, 41))
    assert archive.stat().st_size < 100_000_000
    import pymupdf
    results = []
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, 'Archive CRC failure.'
        names = set(z.namelist())
        assert all(n.startswith(PREFIX) and '..' not in PurePosixPath(n).parts for n in names)
        media = [n for n in names if '/media/' in n or Path(n).suffix.lower() in
                 ('.mp4', '.m4a', '.wav', '.mp3', '.aac', '.webm', '.mov', '.ogg')]
        assert not media, media
        private = [n for n in names if any(part in ('.git', '.env', '.DS_Store', '__MACOSX')
                                         for part in PurePosixPath(n).parts)]
        assert not private, private
        for name in VIDEO_PAGES:
            assert PREFIX + 'teaching/2105603/' + name not in names
        manifest = json.loads(z.read(PREFIX + 'MANIFEST.json'))
        assert set(names) == {PREFIX + n for n in manifest} | {PREFIX + 'MANIFEST.json'}
        for name, digest in manifest.items():
            assert sha(z.read(PREFIX + name)) == digest, name
        for name, page_count in PDFS.items():
            rel = 'teaching/2105603/files/' + name
            data = z.read(PREFIX + rel)
            assert data == (COURSE / 'files' / name).read_bytes(), name
            assert len(pymupdf.open(stream=data, filetype='pdf')) == page_count, name
            results.append({'file': rel, 'verification': 'byte-identical to staged public PDF',
                            'sha256': sha(data), 'pages': page_count})
        for name in HTML:
            rel = 'teaching/2105603/' + name
            source = (COURSE / name).read_text()
            data = z.read(PREFIX + rel)
            assert data.decode() == permitted_html_rewrites(source), name
            results.append({'file': rel, 'verification': 'exact match after documented offline link rewrites only',
                            'public_sha256': sha(source.encode()), 'offline_sha256': sha(data)})
        hub = z.read(PREFIX + 'teaching/2105603/week04-study.html').decode()
        anchors = [f'https://www.skhgroup.net/teaching/2105603/week04-video.html#slide-{n}' for n in (16, 30)]
        assert all(link in hub for link in anchors)
        relative_player_links = []
        for name in names:
            if not name.endswith('.html'):
                continue
            text = z.read(name).decode()
            for href in re.findall(r'href=["\']([^"\']+)["\']', text):
                if any(v in href for v in VIDEO_PAGES) and not href.startswith('https://www.skhgroup.net/teaching/2105603/'):
                    relative_player_links.append({'file': name[len(PREFIX):], 'href': href})
        assert not relative_player_links, relative_player_links
        learning = json.loads(z.read(PREFIX + 'teaching/2105603/labs/assets/learning-path.json'))
        session = next(s for s in learning['sessions'] if s['number'] == 4)
        assert session['video'] == 'https://www.skhgroup.net/teaching/2105603/week04-video.html'
        assert session['core'] == ['solids', 'adsorption']
        for lab in ('solids', 'adsorption'):
            assert PREFIX + f'teaching/2105603/labs/{lab}.html' in names
        release = 'teaching/2105603/labs/release-manifest.json'
        assert z.read(PREFIX + release) == (SITE / release).read_bytes()
        report = {
            'status': 'pass',
            'scope': 'Final offline archive integrity and current Week 4 content; no live-server playback claim.',
            'archive': 'teaching/2105603/files/thermodynamics-offline.zip',
            'archive_sha256': sha(archive.read_bytes()), 'archive_bytes': archive.stat().st_size,
            'manifest_files_verified': len(manifest), 'files': results,
            'online_demo_anchors_preserved': anchors,
            'relative_omitted_player_links': relative_player_links,
            'media_files_in_archive': media, 'private_system_files': private,
            'labs_release_manifest_byte_identical': True,
            'session_4_core_labs': session['core'],
            'staged_player_sha256': sha(player.encode()), 'staged_player_chapters': len(chapters),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': 'pass', 'files': report['manifest_files_verified'],
                      'archive_MB': round(report['archive_bytes'] / 1e6, 2)}))


if __name__ == '__main__':
    main()
