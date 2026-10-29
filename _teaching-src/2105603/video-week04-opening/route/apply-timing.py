"""Populate the integrated lesson timing from its final measured media timeline.

Run once the combined video is verified. This changes only the hub's timing
paragraph and can be rerun with a new timeline. Navigation reads this paragraph.
"""
from pathlib import Path
import argparse,json,math,re

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--timeline',type=Path,required=True)
parser.add_argument('--hub',type=Path,default=Path(__file__).with_name('week04-study.html'))
args=parser.parse_args()
raw=json.loads(args.timeline.read_text())
rows=raw if isinstance(raw,list) else raw.get('slides',raw.get('chapters'))
assert isinstance(rows,list) and len(rows)==54,'Expected 14 opening chapters and 40 core slides'
assert [r.get('section') for r in rows[:14]]==['opening']*14
assert [r.get('section') for r in rows[14:]]==['core']*40
assert [r.get('core_slide') for r in rows[14:]]==list(range(1,41))
seconds=float(rows[-1]['end_seconds'])
opening=float(rows[13]['end_seconds'])-float(rows[0]['start_seconds'])
assert math.isfinite(seconds) and seconds>opening>0
assert abs(float(rows[0]['start_seconds']))<.001
for left,right in zip(rows,rows[1:]):
    assert abs(float(left['end_seconds'])-float(right['start_seconds']))<.01

def duration(value):
    m,s=divmod(round(value),60)
    return f'{m} minutes {s:02} seconds'

paragraph=(f'<p id="integrated-timing">The combined recording is <strong>{duration(seconds)}</strong>, '
    f'including <strong>{duration(opening)}</strong> of opening narration. '
    'Add <strong>4 minutes for R1-R3, 100 minutes for core calculations, Labs and reflection, '
    f'and a 10-minute break</strong>: about <strong>{seconds/60+114:.1f} minutes</strong> '
    'if you watch the full recording. The opening plus its notebook pause takes about '
    f'<strong>{opening/60+4:.1f} minutes</strong>; it is already included in this total. '
    'Skipping the optional H recording shortens the lesson. These are planning budgets, '
    'not measured student completion times; record your actual study minutes.</p>')
text=args.hub.read_text()
text,n=re.subn(r'<p id="integrated-timing">.*?</p>',lambda _:paragraph,text,flags=re.S)
assert n==1,'Expected one timing paragraph'
assert '@@' not in text,'Unresolved timing placeholder'
args.hub.write_text(text)
print(json.dumps({'recording_seconds':seconds,'opening_seconds':opening,
    'required_work_minutes':104,'break_minutes':10,'conservative_total_minutes':seconds/60+114,
    'opening_including_notebook_minutes':opening/60+4,'hub':str(args.hub)},indent=2))
