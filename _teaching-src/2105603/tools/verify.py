"""Post-copy check for teaching/2105603/. Run from anywhere:

    python3 _teaching-src/2105603/tools/verify.py

Everything it checks has gone wrong at least once. It reads the published tree
and `_data/act2026.yml` only — it never writes, so it is safe to run on a dirty
working tree before `git add`.

Exit status is 0 if every check passes, 1 otherwise, so it can go in a hook.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
PUB = ROOT / "teaching" / "2105603"
DATA = ROOT / "_data" / "act2026.yml"

fails: list[str] = []
warns: list[str] = []


def fail(msg: str) -> None:
    fails.append(msg)
    print("  FAIL " + msg)


def warn(msg: str) -> None:
    warns.append(msg)
    print("  warn " + msg)


def ok(msg: str) -> None:
    print("  ok   " + msg)


def read_modules(text: str) -> list[dict]:
    """Minimal reader for the `modules:` list in act2026.yml.

    PyYAML is not a dependency of a Jekyll repo and this script has to run on a
    bare python3. The file is written by hand in a fixed shape, so a few regexes
    are enough — and if the shape ever changes, the check below that every
    module has an id and a slides file will notice before anything else does.
    """
    mods: list[dict] = []
    cur: dict | None = None
    in_modules = False
    in_files = False
    for line in text.splitlines():
        if re.match(r"^modules:\s*$", line):
            in_modules = True
            continue
        if in_modules and line and not line[0].isspace():
            break                      # a new top-level key ends the list
        if not in_modules:
            continue
        if re.match(r"^  - id:", line):
            cur = {"id": line.split(":", 1)[1].strip(), "files": []}
            mods.append(cur)
            in_files = False
            continue
        if cur is None:
            continue
        if re.match(r"^    files:\s*$", line):
            in_files = True
            continue
        m = re.match(r"^    slides:\s*(\S+)", line)
        if m:
            cur["slides"] = m.group(1)
            in_files = False
            continue
        if in_files:
            m = re.match(r"^\s+file:\s*(\S+)", line)
            if m:
                cur["files"].append(m.group(1))
        if re.match(r"^    \w+:", line) and not re.match(r"^    files:", line):
            in_files = False
    return mods


print(f"repository root: {ROOT}")

# ---------------------------------------------------------------- structure --
if not PUB.is_dir():
    sys.exit(f"FAIL no {PUB} — are you running this from inside the repo?")
if not DATA.is_file():
    sys.exit(f"FAIL no {DATA}")

modules = read_modules(DATA.read_text(encoding="utf-8"))
print(f"\n_data/act2026.yml — {len(modules)} modules")
if len(modules) != 6:
    fail(f"expected 6 modules, parsed {len(modules)}: {[m['id'] for m in modules]}")
else:
    ok("six modules: " + ", ".join(m["id"] for m in modules))

# ------------------------------------------------------------------- decks --
print("\ndecks")
for m in modules:
    name = m.get("slides")
    if not name:
        fail(f"module {m['id']} has no `slides:` key")
        continue
    path = PUB / name
    if not path.is_file():
        fail(f"{name} named in act2026.yml but missing from teaching/2105603/")
        continue
    html = path.read_text(encoding="utf-8", errors="ignore")

    n_notes = html.count('class="notes"')
    n_cdn = html.count("cdn.jsdelivr")
    if n_notes:
        fail(f"{name}: {n_notes} speaker-note blocks are public "
             f"— re-render with --profile public")
    if n_cdn:
        fail(f"{name}: {n_cdn} CDN links — run tools/vendor-katex.py _site")

    # Every local asset the deck asks for must be on disk. A renamed figure is
    # the usual cause and it shows as a blank panel, not as an error.
    missing = []
    for ref in set(re.findall(r'(?:src|href)="((?:figures|site_libs)/[^"?#]+)"', html)):
        if not (PUB / ref).exists():
            missing.append(ref)
    if missing:
        for ref in sorted(missing)[:8]:
            fail(f"{name}: references {ref}, which does not exist")
        if len(missing) > 8:
            fail(f"{name}: …and {len(missing) - 8} more missing assets")

    if not (n_notes or n_cdn or missing):
        n_fig = len(set(re.findall(r'src="(figures/[^"?#]+)"', html)))
        ok(f"{name}: no notes, no CDN, {n_fig} figures all present")

# ------------------------------------------------------------- course page --
print("\nJekyll course page")
page = PUB / "index.html"
if not page.is_file():
    fail("teaching/2105603/index.html is gone — restore it from git")
else:
    head = page.read_text(encoding="utf-8", errors="ignore")[:400]
    if "layout: default" not in head:
        fail("teaching/2105603/index.html no longer has Jekyll front matter — "
             "a Quarto render overwrote it; restore it from git")
    else:
        ok("index.html still has its Jekyll front matter")

# ----------------------------------------------------------------- downloads --
print("\ndownloads named in act2026.yml")
files_dir = PUB / "files"
listed: set[str] = set()
for m in modules:
    for f in m["files"]:
        listed.add(f)
        if not (files_dir / f).is_file():
            fail(f"module {m['id']} lists files/{f}, which does not exist")
if not fails:
    ok(f"{len(listed)} download files, all present")

present = {p.name for p in files_dir.iterdir() if p.is_file()} if files_dir.is_dir() else set()
for extra in sorted(present - listed):
    warn(f"files/{extra} is on disk but not listed in act2026.yml — it will not "
         f"be linked from the course page")

# ------------------------------------------------------------------- theme --
print("\nshared assets")
themes = sorted((PUB / "site_libs/revealjs/dist/theme").glob("quarto-*.css"))
wanted = set()
for m in modules:
    if m.get("slides") and (PUB / m["slides"]).is_file():
        html = (PUB / m["slides"]).read_text(encoding="utf-8", errors="ignore")
        wanted |= set(re.findall(r"theme/(quarto-[0-9a-f]+\.css)", html))
have = {p.name for p in themes}
if wanted - have:
    fail("missing compiled theme(s): " + ", ".join(sorted(wanted - have)) +
         " — publish.py must merge site_libs/, not replace it")
else:
    ok(f"{len(wanted)} compiled theme file(s) referenced, all present")

katex = PUB / "site_libs/katex/katex.min.js"
if not katex.is_file():
    fail("site_libs/katex/katex.min.js missing — equations will not render offline")
else:
    ok(f"vendored KaTeX present ({katex.stat().st_size // 1024} kB)")

# ------------------------------------------------------------------ verdict --
print()
if fails:
    print(f"{len(fails)} problem(s) — do not push")
    sys.exit(1)
print(f"all checks passed{f', {len(warns)} warning(s)' if warns else ''} — safe to push")
