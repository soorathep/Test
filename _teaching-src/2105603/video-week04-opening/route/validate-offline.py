"""Verify the final Week 4 offline archive against the staged public course.

Run with the absolute research interpreter after tools/build-offline.py.
Set SKH_WEBSITE_DIR to the public website checkout. The JSON report uses
repository-relative paths and contains no machine-specific paths.
"""
from pathlib import Path, PurePosixPath
import argparse
import ast
import hashlib
import json
import os
import re
import zipfile


ROOT = next((p for p in Path(__file__).resolve().parents if (p / 'asynchronous-week04').is_dir()), Path.cwd())
SITE = Path(os.environ.get("SKH_WEBSITE_DIR", str(Path.home() / "Documents/GitHub/Test")))
COURSE = SITE / "teaching/2105603"
PREFIX = "thermodynamics-offline/"
PDFS = {
    "week04-video-slides.pdf": 54,
    "postmidterm-04-slides.pdf": 40,
    "preclass-week-04.pdf": 3,
    "week04-practice.pdf": 6,
    "week04-lab-guide.pdf": 4,
    "week04-solutions.pdf": 4,
}
HTML = ("week04-study.html", "week04-questions.html", "postmidterm-04.html", "postmidterm-04-appendix.html")
VIDEO_PAGES = ()  # Read from the final reviewed builder without executing it.


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
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/week04-opening-video/offline-qa.json')
    parser.add_argument('--builder', type=Path, default=Path(__file__).with_name('build-offline.py'))
    args = parser.parse_args()
    global VIDEO_PAGES
    builder_source = args.builder.read_text()
    builder_tree = ast.parse(builder_source)
    rewrites = [ast.literal_eval(n.iter) for n in ast.walk(builder_tree)
                if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                and n.target.id == 'video_page']
    assert len(rewrites) == 1 and isinstance(rewrites[0], tuple)
    VIDEO_PAGES = rewrites[0]
    assert 'week04-video.html' in VIDEO_PAGES and len(VIDEO_PAGES) == len(set(VIDEO_PAGES))
    assert all(isinstance(n, str) and n.endswith('-video.html') for n in VIDEO_PAGES)
    archive = COURSE / 'files/thermodynamics-offline.zip'
    # A finished live player must exist before we accept the offline edition.
    player = (COURSE / 'week04-video.html').read_text()
    chapters_match = re.search(r'<script\b[^>]*id="chapter-data"[^>]*>(.*?)</script>', player, re.S)
    assert chapters_match, 'Staged Week 4 player is missing its chapter data.'
    chapters = json.loads(chapters_match[1])
    assert len(chapters) == 54 and [c['slide'] for c in chapters] == list(range(1, 55))
    opening, core = chapters[:14], chapters[14:]
    assert all(c['section'] == 'opening' and c['core_slide'] is None for c in opening)
    assert [c['anchor'] for c in opening] == [f'opening-{n:02}' for n in range(1, 15)]
    assert all(c['section'] == 'core' for c in core)
    assert [c['core_slide'] for c in core] == list(range(1, 41))
    assert [c['anchor'] for c in core] == [f'slide-{n}' for n in range(1, 41)]
    assert opening[12]['activity'] and opening[12]['activity_minutes'] == 4
    assert sum(c['activity_minutes'] for c in opening) == 4
    assert sum(c['activity_minutes'] for c in core if c['core_slide'] != 20) == 100
    assert core[19]['activity_minutes'] == 10
    assert core[35]['optional_activity'] and core[35]['activity_minutes'] == 0
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
        anchors = ['https://www.skhgroup.net/teaching/2105603/week04-video.html#opening-01']
        anchors += [f'https://www.skhgroup.net/teaching/2105603/week04-video.html#slide-{n}' for n in (16, 30)]
        assert all(link in hub for link in anchors)
        questions = z.read(PREFIX + 'teaching/2105603/week04-questions.html').decode()
        assert 'https://www.skhgroup.net/teaching/2105603/week04-video.html#slide-1' in questions
        assert 'files/week04-video-slides.pdf' in hub
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
            'opening_chapters': len(opening), 'core_slides': len(core),
            'new_and_legacy_anchors_preserved': True,
            'builder_sha256': sha(builder_source.encode()),
            'omitted_video_pages_from_final_builder': list(VIDEO_PAGES),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': 'pass', 'files': report['manifest_files_verified'],
                      'archive_MB': round(report['archive_bytes'] / 1e6, 2)}))


if __name__ == '__main__':
    main()
