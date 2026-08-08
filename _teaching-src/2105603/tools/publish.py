"""Copy the rendered deck into the published tree.

Quarto's website project writes an index.html and a search.json alongside the
deck. `teaching/2105603/index.html` is the Jekyll course page, so rendering
straight into that folder would overwrite it. This script copies only what the
deck actually needs.

    quarto render eos.qmd --profile public --output-dir _site
    python3 tools/vendor-katex.py _site
    python3 tools/publish.py
"""
import pathlib
import shutil
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "_site"
DST = pathlib.Path(__file__).resolve().parents[3] / "teaching" / "2105603"

KEEP_FILES = ["eos.html"]
KEEP_DIRS = ["site_libs", "figures"]
NEVER = {"index.html", "search.json"}   # would clobber the Jekyll course page


def main():
    if not SRC.exists():
        sys.exit(f"no render found at {SRC} — run quarto render first")
    DST.mkdir(parents=True, exist_ok=True)

    for name in KEEP_FILES:
        src = SRC / name
        if not src.exists():
            sys.exit(f"missing {src}")
        shutil.copy2(src, DST / name)
        print("copied", name)

    for name in KEEP_DIRS:
        src = SRC / name
        if not src.exists():
            continue
        dst = DST / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print("copied", name + "/")

    for name in NEVER:
        stale = DST / name
        if name == "index.html":
            text = stale.read_text(encoding="utf-8", errors="ignore") if stale.exists() else ""
            if stale.exists() and "layout: default" not in text[:200]:
                sys.exit(f"{stale} is not the Jekyll course page any more — restore it from git")

    html = (DST / "eos.html").read_text(encoding="utf-8")
    for bad, why in [('class="notes"', "speaker notes are still in the published deck — "
                                        "render with --profile public"),
                     ("cdn.jsdelivr", "KaTeX still points at the CDN — run tools/vendor-katex.py")]:
        if bad in html:
            sys.exit("REFUSING TO PUBLISH: " + why)

    print(f"published to {DST}")


if __name__ == "__main__":
    main()
