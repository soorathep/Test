"""Stage only reviewed course material and reproducible video sources."""
from pathlib import Path
import shutil,json,hashlib
W=Path(__file__).resolve().parents[2];S=Path.home()/"Documents/GitHub/Test"
P=S/"teaching/2105603";T=S/"_teaching-src/2105603"
src=Path(__file__).resolve().parent;out=W/"outputs/week04-opening-video"
qa=json.loads((out/"video-qa.json").read_text())
assert qa["passed"] and qa["chapter_count"]==54 and qa["size_bytes"]<100_000_000
assert json.loads((out/"asr-review.json").read_text())["status"]=="reviewed_no_clear_semantic_mismatch"
def copy(a,b): b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
for name in ["week04-study.html","week04-questions.html"]:
 copy(src/"route"/name,P/name);copy(src/"route"/name,T/name)
copy(out/"week04-video.html",P/"week04-video.html")
copy(src/"route/postmidterm-04.html",P/"postmidterm-04.html")
copy(src/"route/postmidterm-04.qmd",T/"postmidterm-04.qmd")
for name in ["week04-lecture.mp4","week04-poster.png","week04-captions.vtt"]:
 copy(out/name,P/"media/week04"/name)
for name in ["week04-video-slides.pdf","postmidterm-04-slides.pdf"]:
 copy(out/name,P/"files"/name)
for name in ["week04-practice.pdf","week04-lab-guide.pdf","week04-solutions.pdf"]:
 copy(out/"documents"/name,P/"files"/name)
copy(src/"route/build_week04.py",T/"prereading/week04/build_week04.py")
dest=T/"video-week04-opening"
for name in ["README.txt","opening-draft.json","core-narration-patches.json","script-contract.json","narration.json","prepare_combined.py","build-narration.py","build-video.py","qa-audio.py","qa-audio-reviews.json","reviewed-pdf.sha256","base-core-slides.pdf","stage-publication.py"]:
 copy(src/name,dest/name)
copy(src/"figures/build_frames.py",dest/"figures/build_frames.py")
for name in ["build-video-page.py","test-player.mjs","README.txt"]:
 copy(src/"player"/name,dest/"player"/name)
for name in ["apply-timing.py","update-course-links.py","build-offline.py","update-core-slides.py","README.txt"]:
 copy(src/"route"/name,dest/"route"/name)
for name in ["timeline.json","caption-timeline.json","video-qa.json","controller-qa.json","asr-review.json","documents-qa.json"]:
 copy(out/name,dest/"qa"/name)
for name in ["manifest.json","audio-qa.json"]:
 copy(out/"audio"/name,dest/"qa"/("audio-"+name))
for name in ["feedback-opening/README.txt","video-week04/README.md"]:
 path=T/name;s=path.read_text()
 prefix="CURRENT PUBLICATION: The combined opening + core recording is now reproduced from ../video-week04-opening/. This file documents the prior edition and its retained source inputs.\n\n"
 if not s.startswith("CURRENT PUBLICATION:"):path.write_text(prefix+s)
print("Staged integrated video, captions, matching PDFs, corrected core deck, routes and source allowlist.")
