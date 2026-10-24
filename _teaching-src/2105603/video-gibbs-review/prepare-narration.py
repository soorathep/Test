"""Validate the Gibbs review script against the published 26-slide deck."""
from pathlib import Path
import argparse
import hashlib
import json
import re

from bs4 import BeautifulSoup

FOLDER = Path(__file__).resolve().parent
EXPECTED_PDF_SHA256 = "ce1931747b20493413893c43f674f4cfd300952afea32230afc123f1eeb15ef6"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path.home()/"Documents/GitHub/Test")
    parser.add_argument("--draft", type=Path, default=FOLDER/"narration-draft.json")
    parser.add_argument("--output", type=Path, default=FOLDER/"narration.json")
    args = parser.parse_args()
    course = args.site/"teaching/2105603"
    pdf = course/"files/week03-gibbs-review-slides.pdf"
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == EXPECTED_PDF_SHA256, "Review and freeze a changed PDF before narration."
    raw = json.loads(args.draft.read_text())["slides"]
    sections = BeautifulSoup((course/"week03-gibbs-review.html").read_text(), "html.parser").select(".reveal .slides > section")
    assert len(raw) == len(sections) == 26
    entries = []
    for number, (row, slide) in enumerate(zip(raw, sections), 1):
        assert row["number"] == number and row["slide_id"] == slide["id"], (number, row["slide_id"], slide["id"])
        narration = " ".join(row["narration"].split())
        pause = " ".join(row.get("pause_instruction", "").split())
        minutes = row.get("activity_minutes", 0)
        assert narration and "\\" not in narration
        assert not re.search(r"[\u0e00-\u0e7f]", narration+pause), "Student material must be English."
        assert not re.search(r"\d\.\d", narration), "Spell decimal values out for predictable pronunciation."
        assert isinstance(minutes, (int, float)) and minutes >= 0
        assert bool(pause) == bool(minutes), (number, "Activity time and pause instruction must agree.")
        entries.append({**row, "id": f"{number:02d}", "slide": number,
                        "title": slide.find(["h1", "h2"]).get_text(" ", strip=True),
                        "narration": narration, "pause_instruction": pause,
                        "activity_minutes": minutes, "activity": minutes > 0,
                        "stage_start_minute": None, "stage_end_minute": None,
                        "source_pdf_sha256": EXPECTED_PDF_SHA256})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(entries, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"validated_slides": len(entries),
                      "spoken_words": sum(len(e["narration"].split()) for e in entries),
                      "activity_minutes": sum(e["activity_minutes"] for e in entries),
                      "pause_points": [e["slide"] for e in entries if e["activity"]],
                      "pdf_sha256": EXPECTED_PDF_SHA256}))


if __name__ == "__main__":
    main()
