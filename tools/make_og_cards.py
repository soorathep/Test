#!/usr/bin/env python3
"""
Build 1200x630 link-preview cards for Facebook and LinkedIn.

Why this exists
---------------
A journal cover is portrait (760x999, ratio 0.76). Facebook and LinkedIn want
1.91:1 landscape. Handing them the cover directly gets it centre-cropped into a
letterbox that throws away the top and bottom of the artwork, or shrunk into a
small square thumbnail. So each cover gets a purpose-built card instead: the
cover sits whole on the left, the caption sits on the right, in the site's
colours.

Usage
-----
    pip install pillow pyyaml fonttools
    python tools/make_og_cards.py

Reads  _data/covers.yml   (the same file the website reads)
Writes img/og/<stem>.jpg  (one card per cover)

Fonts are fetched once from the Google Fonts GitHub mirror and cached in
tools/.fonts/. Nothing else is needed.
"""
import io, os, re, sys, textwrap, urllib.request, pathlib
import yaml
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = pathlib.Path(__file__).resolve().parent / ".fonts"
OUT = ROOT / "img" / "og"

PRUSSIAN, SODIUM, PAPER, SOFT = "#0E3B5C", "#E8A80B", "#F4F3F0", "#9FB3C4"
W, H = 1200, 630

SOURCES = {
    "Archivo.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/archivo/Archivo%5Bwdth%2Cwght%5D.ttf",
    "SourceSerif4.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/sourceserif4/SourceSerif4%5Bopsz%2Cwght%5D.ttf",
    "IBMPlexMono-Medium.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-Medium.ttf",
}


def font_file(name):
    FONTS.mkdir(exist_ok=True)
    p = FONTS / name
    if not p.exists():
        print("  fetching", name)
        p.write_bytes(urllib.request.urlopen(SOURCES[name]).read())
    return p


def pinned(name, out, axes):
    p = FONTS / out
    if not p.exists():
        f = TTFont(font_file(name))
        instancer.instantiateVariableFont(f, axes, inplace=True)
        f.save(p)
    return str(p)


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def card(cover_path, journal, meta, title, dest):
    im = Image.new("RGB", (W, H), PRUSSIAN)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 6], fill=SODIUM)

    # cover, whole, on the left
    cov = Image.open(cover_path).convert("RGB")
    ch = H - 96
    cw = round(cov.width * ch / cov.height)
    cov = cov.resize((cw, ch), Image.LANCZOS)
    cx, cy = 56, 48
    d.rectangle([cx - 1, cy - 1, cx + cw, cy + ch], outline="#1B5480", width=1)
    im.paste(cov, (cx, cy))

    x = cx + cw + 56
    tw = W - x - 56
    f_eyebrow = ImageFont.truetype(str(font_file("IBMPlexMono-Medium.ttf")), 18)
    f_journal = ImageFont.truetype(pinned("Archivo.ttf", "archivo-700.ttf", {"wght": 700, "wdth": 100}), 40)
    f_title = ImageFont.truetype(pinned("SourceSerif4.ttf", "serif-400.ttf", {"wght": 400, "opsz": 20}), 27)

    y = cy + 6
    d.text((x, y), "JOURNAL COVER", font=f_eyebrow, fill=SODIUM); y += 40
    for ln in wrap(d, journal, f_journal, tw):
        d.text((x, y), ln, font=f_journal, fill=PAPER); y += 48
    y += 6
    d.text((x, y), meta.replace("&amp;", "&"), font=f_eyebrow, fill=SOFT); y += 42
    if title:
        for ln in wrap(d, title, f_title, tw)[:6]:
            d.text((x, y), ln, font=f_title, fill=PAPER); y += 37

    d.text((x, H - 78), "SKH Research Group", font=f_eyebrow, fill=SOFT)
    d.text((x, H - 50), "skhgroup.net", font=f_eyebrow, fill=SODIUM)

    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=88, optimize=True, progressive=True)
    return dest


def main():
    covers = yaml.safe_load((ROOT / "_data" / "covers.yml").read_text(encoding="utf-8"))
    for c in covers:
        src = ROOT / "covers" / c["file"]
        if not src.exists():
            print("  MISSING", src); continue
        dest = OUT / (pathlib.Path(c["file"]).stem + ".jpg")
        card(src, c["journal"].replace("&amp;", "&"), c["meta"], c.get("title", ""), dest)
        print("  %-52s %5.0f KB" % (dest.relative_to(ROOT), dest.stat().st_size / 1024))


if __name__ == "__main__":
    main()
