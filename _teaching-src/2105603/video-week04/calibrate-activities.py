"""Report measured recording time alongside fixed, task-based activity estimates.

This does not stretch or shrink activities to manufacture a 180-minute total.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/"outputs/week04-video/audio/manifest.json").read_text())
expected={4:8,8:6,13:10,15:5,18:22,20:10,25:10,29:5,32:24,36:20,39:10}
assert len(rows)==40
for row in rows:
    assert row["activity_minutes"]==expected.get(row["slide"],0),(row["slide"],row["activity_minutes"])
    assert row["activity"]==(row["slide"] in expected)
recording=(sum(r["duration_seconds"] for r in rows)+2*len(rows))/60
work=sum(v for k,v in expected.items() if k!=20)
assert work==120
report={"recording_minutes":recording,"suggested_independent_minutes":work,
        "break_minutes":10,"approximate_total_minutes":recording+work+10,
        "target_lesson_minutes":180,"work_checkpoint_count":10,
        "activity_estimates":expected,
        "note":"Recording duration is measured. The 120-minute work allowance and 10-minute break are planning estimates, not observed completion times or minimum waiting periods. Activity estimates are fixed by the tasks and are never scaled to force a 180-minute total. Learners retain outputs, move on when ready, and report actual study time in feedback."}
(ROOT/"outputs/week04-video/study-time-qa.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
