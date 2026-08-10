"""Copy the rendered deck(s) into the published tree.

Quarto's website project writes an index.html and a search.json alongside the
decks. `teaching/2105603/index.html` is the Jekyll course page, so rendering
straight into that folder would overwrite it. This script copies only what the
decks actually need.

    quarto render --profile public --output-dir _site      # every deck
    python3 tools/vendor-katex.py _site
    python3 tools/publish.py                               # every deck it finds
    python3 tools/publish.py vle.html                      # or just one

WHY site_libs AND figures ARE MERGED, NOT REPLACED
--------------------------------------------------
Six decks share one `teaching/2105603/site_libs/`, and Quarto content-hashes
the compiled theme: `quarto-becc5085…css` for Module 1, `quarto-44ab3010…css`
for Modules 2-6. The earlier version of this script did `rmtree` + `copytree`
on site_libs. Rendering one module alone and publishing it therefore deleted
the theme file every other module's HTML points at, and those decks came up
unstyled — with no error, because the HTML and the images were all still there.

The same argument applies to `figures/`: a single-module render only puts that
module's figures in `_site/figures/`, so replacing the folder would strip the
other 100-odd images.

So both directories are copied file by file. Nothing in the destination is
removed. A figure that has been renamed upstream leaves its old file behind;
that is deliberate, and cheaper than the failure mode above. Delete stale files
by hand, checking git status first.
"""
import pathlib
import shutil
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "_site"
DST = pathlib.Path(__file__).resolve().parents[3] / "teaching" / "2105603"

# Every deck in the folder, unless the caller names one. Hard-coding a single
# file meant the second module was rendered, checked, and then not copied.
DECKS = [
    "eos.html",        # Module 1  Evolution of Equations of State
    "fugacity.html",   # Module 2  Fugacity and the Equilibrium Criterion
    "solution.html",   # Module 3  Solution Thermodynamics
    "vle.html",        # Module 4  Vapour-Liquid Equilibrium of Mixtures
    "stability.html",  # Module 5  Phase Stability and Complex Equilibria
    "reaction.html",   # Module 6  Chemical Equilibrium
]
MERGE_DIRS = ["site_libs", "figures"]
NEVER = {"index.html", "search.json"}   # would clobber the Jekyll course page


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

    wanted = sys.argv[1:] or DECKS
    decks = [n for n in wanted if (SRC / n).exists()]
    if not decks:
        sys.exit(f"no rendered deck found in {SRC} — run quarto render first")
    missing = [n for n in wanted if n not in decks]
    if missing and len(sys.argv) > 1:
        sys.exit("asked to publish " + ", ".join(missing) + " but they are not in _site")
    if missing:
        print("not rendered this time, left as they are:", ", ".join(missing))

    # Check before copying. A deck that still carries speaker notes should not
    # reach teaching/ even for the second it would take to overwrite it again.
    for name in decks:
        html = (SRC / name).read_text(encoding="utf-8")
        for bad, why in [('class="notes"',
                          "speaker notes are still in the rendered deck — "
                          "render with --profile public"),
                         ("cdn.jsdelivr",
                          "KaTeX still points at the CDN — run tools/vendor-katex.py _site")]:
            if bad in html:
                sys.exit(f"REFUSING TO PUBLISH {name}: " + why)

    page = DST / "index.html"
    if page.exists():
        head = page.read_text(encoding="utf-8", errors="ignore")[:200]
        if "layout: default" not in head:
            sys.exit(f"{page} is not the Jekyll course page any more — restore it from git")

    for name in decks:
        shutil.copy2(SRC / name, DST / name)
        print("copied", name)

    for name in MERGE_DIRS:
        src = SRC / name
        if not src.exists():
            continue
        added, updated = merge_tree(src, DST / name)
        print(f"merged {name}/  {added} new, {updated} changed")

    for name in NEVER & {p.name for p in SRC.iterdir()}:
        if name != "index.html":
            print(f"skipped {name} (would clobber the Jekyll page or its search index)")

    print(f"published to {DST}")


if __name__ == "__main__":
    main()
