"""Copy the rendered deck(s) into the published tree.

Quarto's website project writes an index.html and a search.json alongside the
decks. `teaching/seminars/index.html` is the Jekyll listing page, so rendering
straight into that folder would overwrite it. This script copies only what the
decks actually need.

    quarto render --profile public --output-dir _site   # every deck
    python3 tools/publish.py                            # every deck it finds
    python3 tools/publish.py conferences.html           # or just one

site_libs/ is MERGED, not replaced. Quarto content-hashes the compiled theme,
so every deck in this folder points at its own `quarto-<hash>.css` inside one
shared site_libs/. Replacing the folder while publishing a single deck would
delete the theme file the other decks reference, and those decks would come up
unstyled with no error at all — the HTML and the images would still be there.
Nothing in the destination is removed; delete stale files by hand after
checking `git status`.
"""
import pathlib
import shutil
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "_site"
DST = pathlib.Path(__file__).resolve().parents[3] / "teaching" / "seminars"

MERGE_DIRS = ["site_libs"]
NEVER = {"index.html", "search.json"}   # would clobber the Jekyll listing page


def merge_tree(src: pathlib.Path, dst: pathlib.Path) -> tuple[int, int]:
    """Copy src over dst without deleting anything already in dst."""
    added = updated = 0
    for s in sorted(p for p in src.rglob("*") if p.is_file()):
        d = dst / s.relative_to(src)
        if d.exists():
            if d.stat().st_size == s.stat().st_size and d.read_bytes() == s.read_bytes():
                continue
            updated += 1
        else:
            added += 1
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    return added, updated


def main():
    if not SRC.exists():
        sys.exit(f"no render found at {SRC} — run quarto render first")
    DST.mkdir(parents=True, exist_ok=True)

    # Every deck in _site unless the caller names one. Discovered rather than
    # hard-coded, so adding a seminar does not mean editing this file.
    found = sorted(p.name for p in SRC.glob("*.html") if p.name not in NEVER)
    wanted = sys.argv[1:] or found
    decks = [n for n in wanted if (SRC / n).exists() and n not in NEVER]
    if not decks:
        sys.exit(f"no rendered deck found in {SRC} — run quarto render first")
    missing = [n for n in wanted if n not in decks]
    if missing:
        sys.exit("asked to publish " + ", ".join(missing) + " but they are not in _site")

    # Check before copying. A deck that still carries speaker notes should not
    # reach teaching/ even for the second it would take to overwrite it again.
    for name in decks:
        html = (SRC / name).read_text(encoding="utf-8")
        if 'class="notes"' in html:
            sys.exit(f"REFUSING TO PUBLISH {name}: speaker notes are still in the "
                     "rendered deck — render with --profile public")

    page = DST / "index.html"
    if page.exists():
        head = page.read_text(encoding="utf-8", errors="ignore")[:200]
        if "layout: default" not in head:
            sys.exit(f"{page} is not the Jekyll listing page any more — restore it from git")

    for name in decks:
        shutil.copy2(SRC / name, DST / name)
        print("copied", name)

    for name in MERGE_DIRS:
        src = SRC / name
        if not src.exists():
            continue
        added, updated = merge_tree(src, DST / name)
        print(f"merged {name}/  {added} new, {updated} changed")

    print(f"published to {DST}")


if __name__ == "__main__":
    main()
