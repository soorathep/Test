# Guide: Adding a New Paper Announcement

How this site actually routes content, and the exact steps to add a new paper.

---

## 1. Decide which of the two things you are adding

These are **independent**. Most papers are only the first.

| | News post | Journal cover |
|---|---|---|
| **What it is** | An announcement that a paper is out | Cover art an editor selected for an issue |
| **Where it appears** | `/news/` page + "Latest → News" on the home page | Home page cover strip + Recognition → *Journal cover art* gallery |
| **What you edit** | A file in `_posts/` | An entry in `_data/covers.yml` + a JPEG in `covers/` |

> **Do not add a `covers.yml` entry for a paper that did not get a cover.** It will show up in the Recognition gallery as a broken image and inflate the cover count. If the paper has no cover, you only do Section 2.

---

## 2. Add the news post

### Step 1 — Create the file

Filename: `_posts/YYYY-MM-DD-short-slug.md`

The date in the filename must match the `date:` in the front matter, and should be the **announcement date** (usually today), not the journal's publication date.

### Step 2 — Front matter

```yaml
---
title: "Paper title, sentence case"
date: 2026-07-22
description: "One or two sentences: what the paper does and why it matters. Shown on the news list, the home page, and in link previews."
tag: Paper
kind: news
image: /img/og/short-slug.jpg
---
```

**Field notes — these are the ones that break things:**

- **`kind: news`** — required. `news.html` filters with `where: "kind", "news"`. Any other value (`paper`, `article`, missing) and the post will not appear on the News page at all. Use `kind: essay` only for the Essays page.
- **`tag:`** — free label shown next to the date. In use: `Paper`, `Seminar`, `Perspective`.
- **`image:`** — path to the OG card. Used for `og:image` / `twitter:image` in `_layouts/default.html`. It is **not** rendered inside the post body.
- **`layout:`** — omit it. `_config.yml` already applies `layout: post` to everything in `_posts/`.
- **`research_domain:`** — has no effect. It belongs to the unused `post_v2` layout. Leave it out.

### Step 3 — Body

Markdown, no H1 (the layout renders the title). Convention across existing posts:

- Open with the problem in plain language — 1–2 paragraphs, no heading.
- Use `>` blockquotes for the paper's core framework or triad.
- Use `##` for two or three substantive sections.
- Close with `## Read the paper` (or `## Read the review`) containing the full author list, journal, and DOI link.

### Step 4 — OG card

1200×630 JPEG at `img/og/short-slug.jpg`.

House style (see `img/og/alloy-zinc-anodes-review.jpg` as reference):

| Element | Value |
|---|---|
| Background | `#F4F5F3` |
| Headline | `#101418`, bold sans, ~58 px |
| Subhead | `#0E3B5C` (Prussian), bold sans, ~36 px |
| Accent — gold dash, box letters | `#E8A80B` (Sodium) |
| Secondary text | `#6E7880` |
| Box borders | `#D6D8D5`, 1 px |
| Margin | 70 px all sides |
| Eyebrow | gold dash + `REVIEW` / `ARTICLE` in mono, then journal · year · locator |
| Footer | `DOI ...   ·   skhgroup.net` in mono |

Layout is a three-box row across the lower half, each with a single gold capital letter, a Prussian title, and two lines of grey detail, joined by grey arrows. Box width `313`, gap `60` — this exactly fills the 1060 px between margins. Widen the boxes and the third one runs off the canvas.

> This card is **not** produced by `tools/make_og_cards_v2.py`. That script only reads `covers.yml` and generates cards for journal covers. News-post cards are made separately.

---

## 3. Add a journal cover — only if the paper got one

### Step 1 — Prepare the image

760 px wide JPEG, ~84 quality, saved to `covers/Journal_Name_YEAR.jpg`.

### Step 2 — Add to `_data/covers.yml`

Newest first, at the top of the file:

```yaml
- file: Journal_Name_2026.jpg
  journal: Journal Name
  meta: Vol 15, No 3 · 15 September 2026 · Front cover
  year: 2026
  alt: Journal Name cover, September 2026
  title: Paper title as it appears on the cover
```

Use `&amp;` for ampersands in `journal:` (e.g. `Batteries &amp; Supercaps`).

This one file drives the home-page strip, the Recognition gallery, the cover count, and the year range in the Recognition heading. Nothing else to edit.

### Step 3 — Generate the cover OG card

```bash
cd ~/Documents/GitHub/Test
pip install pillow pyyaml fonttools
python tools/make_og_cards_v2.py
```

Writes `img/og/Journal_Name_YEAR.jpg` for every entry in `covers.yml`. Requires network access on first run to fetch Archivo, Source Serif 4, and IBM Plex Mono into `tools/.fonts/`.

---

## 4. Commit and push

```bash
cd ~/Documents/GitHub/Test

git add _posts/2026-07-22-short-slug.md
git add img/og/short-slug.jpg
# only if there is a cover:
# git add covers/Journal_Name_2026.jpg _data/covers.yml img/og/Journal_Name_2026.jpg

git commit -m "Add paper: short description"
git push origin main
```

GitHub Pages rebuilds in roughly 1–3 minutes. Hard-refresh with **Cmd + Shift + R** — the browser caches aggressively and a normal reload will show you the old page.

---

## Troubleshooting

**Post does not appear on `/news/` at all**
→ `kind:` is not `news`. This is the single most common cause.

**Post appears with the wrong date, or in the wrong position**
→ `date:` in the front matter disagrees with the filename. The list sorts by `date:`.

**Paper shows up in the Recognition cover gallery**
→ It has an entry in `covers.yml`. Remove it unless the paper genuinely received cover art.

**Broken image icon in the cover gallery**
→ `covers.yml` names a file that is not in `covers/`.

**Link preview shows the generic site image**
→ `image:` is missing, or the path does not start with `/`.

**Changes pushed but the site looks unchanged**
→ Check the build at `https://github.com/<user>/<repo>/actions`. Yellow = building, green = done, red = the build failed and the site is still serving the previous version.

**GitHub Desktop: "A lock file already exists in the repository"**
→ Quit GitHub Desktop entirely (Cmd+Q), then in Terminal:
```bash
cd ~/Documents/GitHub/Test && rm -f .git/index.lock
```
Reopen and retry.

**`git push` asks for a username and password, then fails**
→ GitHub no longer accepts password authentication over HTTPS. Use GitHub Desktop, or `gh auth login`, or switch the remote to SSH.

---

## Reference: front matter across the site

| `kind` | Appears on | Also needs |
|---|---|---|
| `news` | `/news/` and home page "Latest" | `tag`, `image` |
| `essay` | `/essays/` and home page "Essays" | `tag`, `image`, optionally `series` |

`series:` groups essays and enables previous/next navigation in the post layout. Not used for papers.
