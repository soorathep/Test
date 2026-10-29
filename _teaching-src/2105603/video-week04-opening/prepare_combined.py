"""Combine reviewed opening narration with the existing core lesson."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
opening=json.loads((HERE/"opening-draft.json").read_text())
core=json.loads((ROOT/"asynchronous-week04/narration.json").read_text())
patch={x["slide"]:x for x in json.loads((HERE/"core-narration-patches.json").read_text())}
assert len(opening)==14 and len(core)==40
rows=[]
for i,e in enumerate(opening,1):
 assert e["slide"]==i
 rows.append({**e,"section":"opening","core_slide":None,"anchor":f"opening-{i:02d}"})
for original in core:
 e=dict(original);n=e["slide"]
 if n in patch:
  e["narration"]=patch[n]["narration"];e["title"]=patch[n]["title"]
 e.update(number=n+14,id=f"{n+14:02d}",slide=n+14,section="core",core_slide=n,anchor=f"slide-{n}")
 if n==36:
  e.update(activity=True,activity_minutes=0,optional_activity_minutes=20,pause_instruction="Choose your route. Go to core slide 39 for the required exit ticket, or spend about 20 extra minutes on optional H1–H4 before continuing to its check.")
 rows.append(e)
assert [x["slide"] for x in rows]==list(range(1,55))
assert sum(e["activity_minutes"] for e in rows if e["core_slide"]!=20)==104
assert rows[33]["core_slide"]==20 and rows[33]["activity_minutes"]==10
for e in rows:
 e["narration"]=" ".join(e["narration"].split())
 assert "—" not in e["narration"]
(HERE/"narration.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n")
print("54 chapters prepared; required work 104 min, break 10 min; core H optional 20 min")
