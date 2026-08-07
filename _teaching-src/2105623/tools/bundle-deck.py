#!/usr/bin/env python3
"""Build a single self-contained HTML file for one deck.

Why this exists
---------------
Quarto's `embed-resources: true` inlines reveal.js, its plugins and every image,
but it silently drops a custom SCSS theme — the deck comes out unstyled. So this
script renders twice and stitches the result:

  1. a normal render, which compiles theme/teal-amber.scss to a .css file
  2. an embed-resources render, which inlines everything except that .css
  3. the compiled CSS is injected into the head of (2)

The output is one file with no external requests: it works offline, over email,
and dropped straight into the Jekyll site with no shared asset folder.

Usage (from the project root):

    python3 tools/bundle-deck.py w01            # -> dist/w01.html
    python3 tools/bundle-deck.py w01 --public   # strips speaker notes

Always use --public for anything that goes on the website.
"""
import argparse
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(cmd):
    print("  $", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit(f"failed: {' '.join(cmd)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", help="deck stem, e.g. w01")
    ap.add_argument("--public", action="store_true",
                    help="strip speaker notes (required for the public website)")
    ap.add_argument("--out", default="dist",
                    help="output directory, relative to the project root (default: dist)")
    args = ap.parse_args()

    src = ROOT / f"{args.deck}.qmd"
    if not src.exists():
        sys.exit(f"no such deck: {src}")

    base = "public" if args.public else ""
    build = ROOT / "_bundle"
    shutil.rmtree(build, ignore_errors=True)

    # 1 — normal render, to obtain the compiled theme CSS
    print("[1/3] compiling the theme")
    run(["quarto", "render", src.name,
         *(["--profile", base] if base else []),
         "--output-dir", "_bundle/linked"])
    css_files = list((build / "linked").rglob("theme/quarto-*.css"))
    if not css_files:
        sys.exit("could not find the compiled theme CSS")
    theme_css = css_files[0].read_text(encoding="utf-8")
    print(f"      {len(theme_css) // 1024} KB of CSS")

    # 2 — self-contained render
    print("[2/3] rendering self-contained")
    run(["quarto", "render", src.name,
         "--profile", f"{base},inline" if base else "inline",
         "--output-dir", "_bundle/inlined"])
    html_path = build / "inlined" / f"{args.deck}.html"
    html = html_path.read_text(encoding="utf-8")

    # 3 — inject
    print("[3/3] injecting the theme")
    if "</head>" not in html:
        sys.exit("unexpected HTML: no </head>")
    html = html.replace("</head>", f"<style>\n{theme_css}\n</style>\n</head>", 1)

    out_dir = (ROOT / args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.deck}.html"
    out.write_text(html, encoding="utf-8")
    shutil.rmtree(build, ignore_errors=True)

    # sanity checks
    notes = len(re.findall(r'<(?:div|aside)[^>]*class="(?:[^"]*\s)?notes(?:\s[^"]*)?"', html))
    links = len(re.findall(r'<link[^>]+href="(?!data:)[^"]+\.css"', html))
    print(f"\n  {out}  ({out.stat().st_size // 1024} KB)")
    print(f"  external stylesheets : {links}   (must be 0)")
    print(f"  speaker-note blocks  : {notes}"
          f"   {'(must be 0 for --public)' if args.public else ''}")
    if links:
        sys.exit("ERROR: the file is not self-contained")
    if args.public and notes:
        sys.exit("ERROR: speaker notes survived the public build")


if __name__ == "__main__":
    main()
