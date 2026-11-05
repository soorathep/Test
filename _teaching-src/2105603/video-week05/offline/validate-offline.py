"""Verify the staged Week 5 student offline package without changing public files."""
from pathlib import Path, PurePosixPath
import argparse
import ast
import hashlib
import json
import re
import zipfile

PREFIX = 'thermodynamics-offline/'
BASE = 'https://www.skhgroup.net/teaching/2105603/'
PDFS = {'postmidterm-05-slides.pdf': 32, 'week05-practice.pdf': 6,
        'week05-lab-guide.pdf': 2, 'week05-solutions.pdf': 5,
        'week04-video-slides.pdf': 54, 'postmidterm-04-slides.pdf': 40,
        'week04-practice.pdf': 6, 'week04-lab-guide.pdf': 4, 'week04-solutions.pdf': 4}
HTML = ('week05-study.html', 'postmidterm-05.html',
        'labs/learning-path.html', 'labs/assessments.html',
        'week04-study.html', 'week04-questions.html',
        'postmidterm-04.html', 'postmidterm-04-appendix.html')
APPROVED = ('learning-path.html', 'assessments.html',
            'assets/learning-guide.js', 'assets/learning-path.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rewrite_html(source, video_pages):
    source = re.sub(r'<link\b[^>]*href=["\']https://fonts\.(?:googleapis|gstatic)\.com[^>]*>', '', source)
    source = source.replace('../files/thermodynamics-offline.zip', '/README.txt')
    for name in video_pages:
        pattern = r'href=(["\'])(?:\.\./|\./|/teaching/2105603/)?' + re.escape(name) + r'([?#][^"\']*)?\1'
        source = re.sub(pattern, lambda m: 'href=' + m[1] + BASE + name + (m[2] or '') + m[1], source)
    for name in ('eos', 'fugacity', 'solution', 'vle', 'stability', 'reaction'):
        source = source.replace('files/' + name + '-slides.pdf', name + '.html')
    return re.sub(r'href="(?:\./)?files/[^"\n]+\.zip"', 'href="/README.txt"', source)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site', type=Path, required=True)
    p.add_argument('--archive', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--builder', type=Path, default=Path(__file__).with_name('build-offline.py'))
    args = p.parse_args()
    site = args.site.expanduser().resolve()
    course = site / 'teaching/2105603'
    archive = args.archive.expanduser().resolve() if args.archive else course / 'files/thermodynamics-offline.zip'
    builder_source = args.builder.read_text()
    tree = ast.parse(builder_source)
    rewrite_loops = [ast.literal_eval(n.iter) for n in ast.walk(tree)
                     if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                     and n.target.id == 'video_page']
    assert len(rewrite_loops) == 1
    videos = rewrite_loops[0]
    assert 'week05-video.html' in videos and len(videos) == len(set(videos))
    player = (course / 'week05-video.html').read_text()
    match = re.search(r'<script\b[^>]*id="chapter-data"[^>]*>(.*?)</script>', player, re.S)
    assert match, 'Missing finished player chapter data'
    chapters = json.loads(match[1])
    assert len(chapters) == 32
    assert [c['slide'] for c in chapters] == list(range(1, 33))
    assert sum(c['activity_minutes'] for c in chapters) == 138
    assert chapters[22]['activity_minutes'] == 10
    assert sum(c['activity_minutes'] for c in chapters if c['slide'] != 23) == 128
    assert archive.stat().st_size < 100_000_000
    import pymupdf
    results = []
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, 'Archive CRC failure'
        names = set(z.namelist())
        assert all(n.startswith(PREFIX) and '..' not in PurePosixPath(n).parts for n in names)
        media = [n for n in names if '/media/' in n or Path(n).suffix.lower() in
                 ('.mp4', '.m4a', '.wav', '.mp3', '.aac', '.webm', '.mov', '.ogg')]
        assert not media, media
        private = [n for n in names if any(part in ('.git', '.env', '.DS_Store', '__MACOSX')
                                         for part in PurePosixPath(n).parts)]
        assert not private, private
        for name in videos:
            assert PREFIX + 'teaching/2105603/' + name not in names
        manifest = json.loads(z.read(PREFIX + 'MANIFEST.json'))
        assert names == {PREFIX + n for n in manifest} | {PREFIX + 'MANIFEST.json'}
        for name, digest in manifest.items():
            assert sha(z.read(PREFIX + name)) == digest, name
        for name, count in PDFS.items():
            rel = 'teaching/2105603/files/' + name
            data = z.read(PREFIX + rel)
            assert data == (course / 'files' / name).read_bytes(), name
            with pymupdf.open(stream=data, filetype='pdf') as pdf:
                assert len(pdf) == count, name
            results.append({'file': rel, 'sha256': sha(data), 'pages': count,
                            'verification': 'byte-identical staged PDF'})
        for name in HTML:
            rel = 'teaching/2105603/' + name
            source = (course / name).read_text()
            data = z.read(PREFIX + rel)
            assert data.decode() == rewrite_html(source, videos), name
            results.append({'file': rel, 'public_sha256': sha(source.encode()),
                            'offline_sha256': sha(data),
                            'verification': 'only documented offline link rewrites'})
        hub = z.read(PREFIX + 'teaching/2105603/week05-study.html').decode()
        anchors = [BASE + f'week05-video.html#slide-{n}' for n in (1, 20, 22, 30)]
        assert all(link in hub for link in anchors)
        week4 = z.read(PREFIX + 'teaching/2105603/week04-study.html').decode()
        old_anchors = [BASE + 'week04-video.html#opening-01']
        old_anchors += [BASE + f'week04-video.html#slide-{n}' for n in (16, 30)]
        assert all(link in week4 for link in old_anchors)
        relative = []
        for name in names:
            if name.endswith('.html'):
                for href in re.findall(r'href=["\']([^"\']+)["\']', z.read(name).decode()):
                    if any(v in href for v in videos) and not href.startswith(BASE):
                        relative.append({'file': name[len(PREFIX):], 'href': href})
        assert not relative, relative
        learning_rel = 'teaching/2105603/labs/assets/learning-path.json'
        learning = json.loads(z.read(PREFIX + learning_rel))
        original_learning = json.loads((site / learning_rel).read_text())
        expected = json.loads(json.dumps(original_learning))
        for session in expected['sessions']:
            for key in ('video', 'supplementalVideo'):
                if session.get(key) and not re.match(r'https?://', session[key]):
                    session[key] = BASE + session[key]
        assert learning == expected, 'Only video URLs may change in offline learning data'
        week5 = next(s for s in learning['sessions'] if s['number'] == 5)
        assert week5['video'] == BASE + 'week05-video.html'
        assert week5['core'] == ['reaction']
        assert PREFIX + 'teaching/2105603/labs/reaction.html' in names
        release_rel = 'teaching/2105603/labs/release-manifest.json'
        public_release = (site / release_rel).read_bytes()
        assert z.read(PREFIX + release_rel) == public_release
        release = json.loads(public_release)
        for name in APPROVED:
            assert release['files'][name] == sha((course / 'labs' / name).read_bytes()), name
        # Offline MANIFEST covers rewritten JSON; public release metadata remains intact.
        report = {
            'status': 'pass', 'scope': 'Local staged archive; no deployment or playback claim',
            'archive': 'teaching/2105603/files/thermodynamics-offline.zip',
            'archive_sha256': sha(archive.read_bytes()), 'archive_bytes': archive.stat().st_size,
            'manifest_files_verified': len(manifest), 'files': results,
            'online_week5_demo_anchors': anchors,
            'preserved_week4_anchors': old_anchors,
            'relative_omitted_player_links': relative, 'media_files': media,
            'private_system_files': private, 'public_release_manifest_retained': True,
            'approved_public_release_hashes_verified': list(APPROVED),
            'session5_core_labs': week5['core'], 'chapters': len(chapters),
            'work_minutes': 128, 'break_minutes': 10,
            'builder_sha256': sha(builder_source.encode()), 'omitted_players': list(videos),
        }
    args.output.expanduser().parent.mkdir(parents=True, exist_ok=True)
    args.output.expanduser().write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': 'pass', 'files': len(manifest),
                      'archive_MB': round(archive.stat().st_size / 1e6, 2)}))


if __name__ == '__main__':
    main()
