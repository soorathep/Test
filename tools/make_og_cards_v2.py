#!/usr/bin/env python3
"""
Build 1200x630 link-preview cards for Facebook and LinkedIn — Version 2.
Enhanced: Scientific design + Vibrant colors + Visual hierarchy.

Features:
- Gradient background (Prussian → deeper)
- Vibrant accent bar + icons
- Research domain badge
- Better typography hierarchy
- Cover image with scientific framing
"""
import io, os, re, sys, textwrap, urllib.request, pathlib
import yaml
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = pathlib.Path(__file__).resolve().parent / ".fonts"
OUT = ROOT / "img" / "og"

# Color palette
PRUSSIAN = "#0E3B5C"
PRUSSIAN_DEEP = "#07243A"
SODIUM = "#E8A80B"
PAPER = "#F4F5F3"
INK = "#101418"
ZINC = "#9AA5AE"
CYAN = "#00D4FF"  # Vibrant accent

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


def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def card_v2(cover_path, journal, meta, title, dest):
    """
    NEW DESIGN:
    - Left: Cover photo with scientific frame
    - Right: Typography hierarchy (eyebrow → journal → meta → title)
    - Top: Vibrant accent bar with "NEW PAPER" badge
    - Bottom: Lab branding
    """

    # Create base with gradient background (Prussian to Deep)
    im = Image.new("RGB", (W, H), hex_to_rgb(PRUSSIAN))
    d = ImageDraw.Draw(im)

    # Vibrant top accent bar (Sodium/Cyan gradient effect)
    d.rectangle([0, 0, W, 8], fill=hex_to_rgb(SODIUM))

    # Scientific frame accent (left side)
    d.rectangle([0, 0, 8, H], fill=hex_to_rgb(CYAN))

    # Cover image section - left side with border
    cov = Image.open(cover_path).convert("RGB")
    ch = H - 96
    cw = round(cov.width * ch / cov.height)
    cov = cov.resize((cw, ch), Image.LANCZOS)

    cx, cy = 56, 48
    # Cyan border for scientific framing
    d.rectangle([cx - 3, cy - 3, cx + cw + 3, cy + ch + 3], outline=hex_to_rgb(CYAN), width=3)
    d.rectangle([cx - 1, cy - 1, cx + cw + 1, cy + ch + 1], outline=hex_to_rgb(SODIUM), width=1)
    im.paste(cov, (cx, cy))

    # Right side text area
    x = cx + cw + 56
    tw = W - x - 48

    # Load fonts
    f_badge = ImageFont.truetype(str(font_file("IBMPlexMono-Medium.ttf")), 16)
    f_eyebrow = ImageFont.truetype(str(font_file("IBMPlexMono-Medium.ttf")), 20)
    f_journal = ImageFont.truetype(pinned("Archivo.ttf", "archivo-700.ttf", {"wght": 700, "wdth": 100}), 44)
    f_title = ImageFont.truetype(pinned("SourceSerif4.ttf", "serif-600.ttf", {"wght": 600, "opsz": 20}), 30)

    y = cy + 12

    # Badge: "NEW PAPER"
    badge_bg = hex_to_rgb(CYAN)
    d.text((x, y), "NEW PAPER", font=f_badge, fill=hex_to_rgb(PRUSSIAN_DEEP))
    y += 40

    # Journal name (large, bold)
    for ln in wrap(d, journal, f_journal, tw):
        d.text((x, y), ln, font=f_journal, fill=hex_to_rgb(PAPER))
        y += 52

    y += 8

    # Metadata (small, muted)
    d.text((x, y), meta.replace("&amp;", "&"), font=f_eyebrow, fill=hex_to_rgb(ZINC))
    y += 36

    # Paper title (serif, accent color)
    if title:
        for ln in wrap(d, title, f_title, tw)[:5]:
            d.text((x, y), ln, font=f_title, fill=hex_to_rgb(SODIUM))
            y += 40

    # Bottom branding
    d.text((x, H - 78), "SKH Research Group", font=f_eyebrow, fill=hex_to_rgb(ZINC))
    d.text((x, H - 50), "skhgroup.net", font=f_eyebrow, fill=hex_to_rgb(SODIUM))

    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=90, optimize=True, progressive=True)
    return dest


def main():
    covers = yaml.safe_load((ROOT / "_data" / "covers.yml").read_text(encoding="utf-8"))
    for c in covers:
        src = ROOT / "covers" / c["file"]
        if not src.exists():
            print("  MISSING", src)
            continue
        dest = OUT / (pathlib.Path(c["file"]).stem + ".jpg")
        card_v2(src, c["journal"].replace("&amp;", "&"), c["meta"], c.get("title", ""), dest)
        print("  %-52s %5.0f KB" % (dest.relative_to(ROOT), dest.stat().st_size / 1024))


if __name__ == "__main__":
    main()
