"""Vendor KaTeX into the rendered deck so equations survive a room with no Wi-Fi.

Quarto's `html-math-method: katex` links katex@latest from jsdelivr. Every
equation in this module is live LaTeX, so a lecture theatre without internet
would lose all of them. This script copies a pinned KaTeX build into
`site_libs/katex/` and repoints the rendered HTML at it.

Run it after every render:

    quarto render eos.qmd --profile public --output-dir _site
    python3 tools/vendor-katex.py _site
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

VERSION = "0.16.11"
CDN = re.compile(r'https://cdn\.jsdelivr\.net/npm/katex@[^/"]+/dist/')


def fetch(dest: pathlib.Path):
    """Download the pinned KaTeX tarball from npm and unpack dist/ into dest."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["npm", "pack", f"katex@{VERSION}"], cwd=tmp, check=True,
                       stdout=subprocess.DEVNULL)
        tgz = next(pathlib.Path(tmp).glob("katex-*.tgz"))
        with tarfile.open(tgz) as t:
            members = [m for m in t.getmembers() if m.name.startswith("package/dist/")]
            t.extractall(tmp, members=members)
        src = pathlib.Path(tmp) / "package" / "dist"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)


def main(site_dir):
    site = pathlib.Path(site_dir)
    dest = site / "site_libs" / "katex"
    if not (dest / "katex.min.js").exists():
        fetch(dest)

    n = 0
    for html in site.glob("*.html"):
        s = html.read_text(encoding="utf-8")
        new = CDN.sub("site_libs/katex/", s)
        if new != s:
            html.write_text(new, encoding="utf-8")
            n += 1
    print(f"vendored KaTeX {VERSION} into {dest}, rewrote {n} file(s)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "_site")
