"""Report measured recording time alongside fixed, task-based activity estimates.

This does not stretch or shrink activities to manufacture a 180-minute total.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/"outputs/week03-video/audio/manifest.json").read_text())
expected={4:9,11:15,13:8,17:9,26:18,28:10,32:8,36:28,40:12,43:8}
assert len(rows)==44
for row in rows:
    assert row["activity_minutes"]==expected.get(row["slide"],0),(row["slide"],row["activity_minutes"])
    assert row["activity"]==(row["slide"] in expected)
recording=(sum(r["duration_seconds"] for r in rows)+2*len(rows))/60
work=sum(v for k,v in expected.items() if k!=28)
assert work==115
report={"recording_minutes":recording,"suggested_independent_minutes":work,
        "break_minutes":10,"approximate_total_minutes":recording+work+10,
        "target_lesson_minutes":180,"work_checkpoint_count":9,
        "activity_estimates":expected,
        "note":"Recording duration is measured. The 115-minute work allowance and 10-minute break are planning estimates, not observed completion times or minimum waiting periods. Activity estimates are fixed by the tasks and are never scaled to force a 180-minute total. Learners retain outputs, move on when ready, and report actual study time in feedback."}
(ROOT/"outputs/week03-video/study-time-qa.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
