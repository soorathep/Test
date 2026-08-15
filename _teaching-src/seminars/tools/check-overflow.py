#!/usr/bin/env python3
"""Measure, rather than eyeball, whether any slide overflows its frame.

A Reveal deck is 1280 x 720 by design, but nothing enforces it: content that
runs past the bottom is simply clipped, and on a laptop preview the clipped
part is often the last card, which is where the point of the slide usually
lives. Checking by eye across forty-five slides does not work — this course has
shipped a deck with seven overflowing slides that three people had looked at.

Reports, per slide, the amount by which the content box exceeds the frame in
each direction, and the identity of the deepest element so the fix has a
target.

    python3 tools/check-overflow.py _site/vle.html
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

W, H = 1280, 720
MARGIN = 0.06                      # matches the deck's `margin:` setting


def main(path):
    url = Path(path).resolve().as_uri()
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(url)
        pg.wait_for_timeout(2500)          # KaTeX and fonts

        # Reveal.getTotalSlides() excludes slides tagged visibility="uncounted"
        # — the appendix — so navigating by index would silently skip exactly
        # the slides nobody has looked at. Walk the DOM instead and drive each
        # section into view by hand.
        n = pg.evaluate(
            "document.querySelectorAll('.reveal .slides > section').length")
        rows = []
        for i in range(n):
            # Prefer Reveal's own navigation: it lays the slide out exactly as
            # a viewer sees it. Only the uncounted slides, which Reveal will
            # not navigate to by index, are forced into view by hand — and
            # forcing changes the layout enough that the two routes disagree
            # by a couple of hundred pixels on figure slides, so never mix them.
            pg.evaluate(
                """(i) => {
                  const secs = document.querySelectorAll('.reveal .slides > section');
                  const s = secs[i];
                  const known = Reveal.getSlides().indexOf(s);
                  if (known >= 0) { Reveal.slide(known); window.__cur = s;
                                    window.__forced = false; return; }
                  // Reveal hides non-present sections with display:none, so
                  // visibility alone leaves every child with a zero-sized box.
                  secs.forEach(x => { x.style.display = ''; });
                  s.classList.remove('future', 'past');
                  s.classList.add('present');
                  s.style.display = 'block';
                  window.__cur = s; window.__forced = true;
                }""", i)
            pg.wait_for_timeout(200)
            r = pg.evaluate(
                """() => {
                  const s = window.__cur;
                  const sr = s.getBoundingClientRect();
                  let bottom = -1e9, right = -1e9, worst = null, worstR = null;
                  for (const el of s.querySelectorAll('*')) {
                    // KaTeX renders a hidden MathML tree for screen readers.
                    // It is visually clipped but still has a bounding box, and
                    // it is routinely wider than the slide — measuring it
                    // produced a 12,958 px 'overflow' on a two-line equation.
                    if (el.closest('.notes')) continue;
                    if (el.closest('.katex-mathml')) continue;
                    // KaTeX draws stretchy delimiters and radicals as SVG
                    // paths whose geometry runs far outside the clip box.
                    // Measure the .katex box itself, not its internals.
                    if (el.tagName === 'svg' || el.closest('svg')) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 && r.height === 0) continue;
                    if (r.bottom > bottom) { bottom = r.bottom; worst = el; worstR = r; }
                    if (r.right > right) { right = r.right; }
                  }
                  const tag = worst ? (worst.tagName.toLowerCase() +
                        (worst.className && typeof worst.className === 'string'
                          ? '.' + worst.className.trim().split(/\\s+/).join('.') : '')) : '';
                  const txt = worst ? (worst.textContent || '').trim().slice(0, 60) : '';
                  return {
                    id: s.id || '(untitled)',
                    title: (s.querySelector('h2') || {}).textContent || '(no h2)',
                    top: sr.top, bottom: sr.bottom, left: sr.left, right: sr.right,
                    cBottom: bottom, cRight: right, worst: tag, worstText: txt,
                    scrollH: s.scrollHeight, clientH: s.clientHeight,
                  };
                }""")
            rows.append(r)
        b.close()

    bad = []
    print(f"{'#':>3}  {'slide':<46}{'over ↓':>9}{'over →':>9}")
    print("-" * 70)
    for i, r in enumerate(rows):
        # the usable frame is the slide box inset by the deck margin
        limit_b = r["bottom"] - MARGIN * H * 0.0     # reveal already insets
        over_b = r["cBottom"] - limit_b
        over_r = r["cRight"] - r["right"]
        flag = ""
        if over_b > 2 or over_r > 2:
            flag = "  <-- OVERFLOW"
            bad.append((i, r, over_b, over_r))
        title = (r["title"] or "").strip()[:44]
        print(f"{i:>3}  {title:<46}{over_b:>9.1f}{over_r:>9.1f}{flag}")

    print("-" * 70)
    if not bad:
        print(f"{len(rows)} slides, none overflowing.")
        return 0
    print(f"{len(bad)} of {len(rows)} slides overflow:\n")
    for i, r, ob, orr in bad:
        print(f"  slide {i}  {r['id']}")
        print(f"    over bottom {ob:+.1f} px, over right {orr:+.1f} px")
        print(f"    deepest element: {r['worst']}")
        print(f"    text: {r['worstText']!r}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "_site/vle.html"))
