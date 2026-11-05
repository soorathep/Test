"""Refresh only four approved public course-navigation asset hashes.

Default is a read-only proposal receipt. --apply updates the staged public
release-manifest. Engine versions, sourceCommit, sourceState, sourceHashes and
all unrelated file entries remain unchanged. This is a local website update,
not an engine release or a storage/NFS operation.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import tempfile

APPROVED = ('learning-path.html', 'assessments.html',
            'assets/learning-guide.js', 'assets/learning-path.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True, help='Local QA receipt path')
    p.add_argument('--apply', action='store_true', help='Apply after public staging is approved')
    args = p.parse_args()
    lab = args.site.expanduser().resolve() / 'teaching/2105603/labs'
    path = lab / 'release-manifest.json'
    original = path.read_bytes()
    before = json.loads(original)
    after = json.loads(original)
    changes = []
    for name in APPROVED:
        if name not in before['files']:
            raise ValueError('Missing existing release entry: ' + name)
        digest = sha((lab / name).read_bytes())
        after['files'][name] = digest
        changes.append({'file': 'teaching/2105603/labs/' + name,
                        'before': before['files'][name], 'after': digest,
                        'changed': before['files'][name] != digest})
    for name, digest in before['files'].items():
        if name not in APPROVED:
            assert after['files'][name] == digest
    assert {k: v for k, v in after.items() if k != 'files'} == {
        k: v for k, v in before.items() if k != 'files'}
    updated = (json.dumps(after, indent=2, ensure_ascii=False) + '\n').encode()
    if args.apply:
        # Avoid overwriting a manifest another actor changed during this operation.
        if path.read_bytes() != original:
            raise RuntimeError('Manifest changed while preparing the update; rerun after coordination.')
        with tempfile.NamedTemporaryFile(dir=lab, prefix='.release-manifest-', delete=False) as f:
            f.write(updated)
            tmp = Path(f.name)
        os.replace(tmp, path)
        assert path.read_bytes() == updated
    receipt = {
        'status': 'applied' if args.apply else 'proposal-only',
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Week 5 public navigation content; four approved file hashes only',
        'manifest': 'teaching/2105603/labs/release-manifest.json',
        'manifest_before_sha256': sha(original),
        'manifest_after_sha256': sha(updated),
        'source_commit_retained': before.get('sourceCommit'),
        'engine_metadata_and_source_hashes_unchanged': True,
        'unrelated_file_entries_unchanged': len(before['files']) - len(APPROVED),
        'changes': changes,
        'claim_limit': 'No engine version change, new source commit, deployment, or NFS archive claim.'
    }
    args.receipt.expanduser().parent.mkdir(parents=True, exist_ok=True)
    args.receipt.expanduser().write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'changed_entries': sum(c['changed'] for c in changes)}))


if __name__ == '__main__':
    main()
