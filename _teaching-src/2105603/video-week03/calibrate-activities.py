"""Fit indicative pause budgets to the 180-minute lesson after exact TTS timing."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'outputs/week03-video/audio/manifest.json'
rows=json.loads(p.read_text())
recording_minutes=(sum(r['duration_seconds'] for r in rows)+2*len(rows))/60
remaining=180-recording_minutes
assert remaining>10
active=[r for r in rows if r['activity'] and r['slide']!=18]
weights=sum(r['activity_minutes'] for r in active)
for row in active:
    row['activity_minutes']=round(row['activity_minutes']/weights*(remaining-10),1)
active[-1]['activity_minutes']=round(remaining-10-sum(r['activity_minutes'] for r in active[:-1]),1)
assert active[-1]['activity_minutes']>0
rows[17]['activity_minutes']=10
p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
report={'recording_minutes':recording_minutes,'suggested_independent_minutes':sum(r['activity_minutes'] for r in rows),'break_minutes':10,'approximate_total_minutes':recording_minutes+sum(r['activity_minutes'] for r in rows),'note':'Indicative budgets include all preparation, calculations, Lab work and reflections. Elapsed study ranges are guidance; the player never automatically resumes a paused activity.'}
(ROOT/'outputs/week03-video/study-time-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
