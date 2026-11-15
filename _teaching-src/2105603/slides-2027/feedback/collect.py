"""Combine saved responses into one CSV per course and session.

Run inside a local clone of the private responses repository:

    git pull
    python3 collect.py            # writes summary/<course>-sNN.csv
"""
from pathlib import Path
import csv
import json

FIELDS = ['received', 'mode', 'exit_ticket', 'pace', 'confidence', 'lab', 'unclear', 'change']
root = Path('responses')
out = Path('summary'); out.mkdir(exist_ok=True)
for session_dir in sorted(p for p in root.glob('*/s*') if p.is_dir()):
    rows = [json.loads(f.read_text(encoding='utf-8')) for f in sorted(session_dir.glob('*.json'))]
    target = out / f'{session_dir.parent.name}-{session_dir.name}.csv'
    with target.open('w', newline='', encoding='utf-8-sig') as fh:      # utf-8-sig so Excel shows Thai
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction='ignore')
        w.writeheader(); w.writerows(sorted(rows, key=lambda r: r.get('received', '')))
    print(target, len(rows), 'responses')
