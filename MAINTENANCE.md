# Maintaining skhgroup.net

```
index.html   the one-pager (~52 KB), plain static HTML
assets/style.css           all styling, shared by the one-pager and the blog
covers/                    journal cover art, 760 px wide
img/                       PI photo
news.html                  the blog index (served at /news/ , not /news.html)
_posts/                    one markdown file per post   <- the part you edit often
_layouts/                  page shell for blog pages
_config.yml                Jekyll settings
```

Two halves, deliberately:

- **The one-pager** is hand-written HTML that GitHub Pages copies through untouched.
  It changes a few times a year.
- **The blog** is Jekyll, built by GitHub automatically on every push. Adding a post is
  adding one markdown file. Nothing to install, nothing to run.

They share `assets/style.css`, so the blog can never drift out of visual sync with the site.

---

## The golden rule

**Never retype an entry. Copy the one above it and change the words.**

Every recurring item on this site is one line following a fixed pattern. Adding a talk
means duplicating a `<div class="item">` line. Adding a cover means duplicating a
`<figure class="cover">` block. That is the entire maintenance model.

---

## What changes, how often, and where

| Content | Frequency | Section | Source of truth |
|---|---|---|---|
| Journal covers | 2–4 / year | `id="recognition"` gallery + home strip | Publisher email with the cover file |
| Invited / plenary talks | 2–3 / year | `id="recognition"`, Talks | CV |
| Selected publications | quarterly | `id="publications"` | Scopus |
| Publication counts (322 / 6,779 / h-47) | yearly | `id="publications"` `<h2>` + note | Scopus |
| People and alumni placements | yearly | `id="people"` | Your records |
| Patents, awards, roles | rare | `id="recognition"`, home callout | CV |
| Instruments | rare | `id="facilities"` | Notion booking calendar |
| **Blog posts** | **whenever** | **`_posts/*.md`** | **You** |

**The CV is upstream of the site.** When the CV changes, the site follows, never the
reverse. Anything on the site that is not traceable to the CV, Scopus, or a file from a
publisher should not be there.

---

## Recipes

### Add a journal cover

1. Resize the publisher's file to **760 px wide, JPEG, quality ~84**. Full-resolution
   covers are 2,500–6,000 px and have no place on a web page. Keep the originals in your
   own archive.
2. Name it `Journal_Name_YEAR.jpg` and put it in `covers/`.
3. In the home strip (`<div class="strip">`), add at the top:
   ```html
   <img src="covers/FILE.jpg" alt="Journal cover, DATE" loading="lazy">
   ```
4. In the gallery (`<div class="covers">`), copy the first `<figure class="cover">` block
   and edit the four fields: `src`, `alt`, `.j` (journal), `.m` (volume, issue, date,
   cover type), `.t` (paper title, omit the span if the cover carries no title).
5. Update the two counts in prose: the gallery `<h2>` and its lede say "twelve".

### Add a talk

In `id="recognition"`, Talks, copy the top `<div class="item">` line:

```html
<div class="item"><div class="yr">YEAR</div><div><h4>ROLE — ACRONYM YEAR, CITY, COUNTRY</h4><p>Full conference name, DD–DD Month YEAR.</p></div></div>
```

Rules learned the hard way:
- **One entry per talk.** Never merge several conferences into one row.
- **Role is Plenary, Keynote, or Invited.** Use what the invitation actually said.
- **Use the real acronym**, the one printed on the conference materials. If a conference
  has no acronym, write its full name.
- **Always name the country.** Singapore is its own country; do not write "Singapore, Singapore".

### Publish a blog post  (the 90-second version)

1. On GitHub, open `_posts/` and click **Add file → Create new file**.
2. Name it `2026-08-14-short-title.md`. **The date in the filename is the publish date.**
   Get it wrong and the post sorts wrong.
3. Type this, then write in markdown underneath:
   ```markdown
   ---
   title: "Whatever it is"
   date: 2026-08-14
   description: "One sentence. Shows on the news index and in link previews."
   tag: Cover
   ---

   Your text. **Bold**, *italic*, [links](https://example.com), ## headings, - bullets.

   ![alt text]({{ site.baseurl }}/covers/FILE.jpg)
   ```
4. Commit. The post is live in about a minute, the news index reorders itself, and
   `feed.xml` updates. You never touch `news.html`.

You can do all of this from a phone. There is no local install and no build command.

**Suggested tags:** Cover, Paper, Talk, People, Lab.

**A post does not have to be an essay.** Three sentences announcing a cover is a post.
The failure mode for an academic blog is not posts that are too short, it is a "Latest
news, March 2024" banner sitting on a 2026 site. Short and alive beats long and abandoned.

### Update the publication counts

One `<h2>` and one `<div class="note">` in `id="publications"`. Change both together or
they will disagree. Refresh the "July 2026" date at the same time.

---

## Two traps that already bit (do not re-introduce)

**1. `.page` is hidden by default.** The one-pager is a JS tab switcher:
`.page{display:none}` and JS adds `.on` to whichever section the hash selects. Blog pages
have no such JS, so `_layouts/default.html` wraps content in `<div class="page on">`.
Drop the `on` and the blog renders as a nav and a footer with nothing between them.

## The permalink trap (this cost an hour once)

`permalink:` in `_config.yml` ends with a `/`. In Jekyll that turns on pretty URLs for
**every HTML page**, not just posts: `news.html` is built to `/news/index.html` and
`/news.html` returns 404. `index.html` and `feed.xml` are exempt, which is why the site
root kept working and only the News link broke.

`news.html` now pins its own `permalink: /news/` in the front matter, so it no longer
depends on that setting. **Link to `/news/`, never `/news.html`.**

## Deploying

Commit to `github.com/soorathep/Test`. GitHub Pages rebuilds on every push. If images do
not appear, the folder is missing or misnamed: paths are case-sensitive.

**Two settings live in `_config.yml` and nowhere else:**

- `baseurl: "/Test"` matches the repo name. Rename the repo and this must change, or every
  blog link 404s. If you point skhgroup.net at Pages, set it to `""`.
- `home_url: "index.html"` is what the nav links back to. Renaming the
  one-pager to `index.html` (recommended eventually, it gives you a clean `/` URL) means
  changing this one line.

If the blog breaks after a rename, it is one of those two lines.

---

## Design decisions worth not undoing

- **No bibliometrics on the home page.** The headline says durability is not a number.
  Counters underneath it contradict that, and they duplicate the Publications page.
  The covers strip does the credibility job better.
- **No hand-copied publication list.** The full record is on Scopus and ORCID. A list
  copied into HTML is stale the week it ships. Only the selected 2024–2026 papers live here.
- **People are named, not counted.** "Sanni, now at Shinshu University" beats "8 PhD
  graduates". The alumni table is the asset; the numeral was not.
- **No embedded base64 images.** The page was 359 KB, of which 298 KB was one photo. It is
  now 61 KB. Keep images in `covers/` and `img/`.

---

## Working with Claude on this

Claude cannot reach the repo. Two ways to work:

1. **Claude Code, repo cloned locally.** Best option. Say "add these three talks" and it
   edits the file and commits. No uploads, no round-trips.
2. **Chat.** At 61 KB the whole file now fits in a message. Better still, paste only the
   section that changes and ask for the replacement block.

Give Claude the **source**, not a summary: the CV, the publisher's cover file, the Scopus
page. Every error worth fixing in this file so far came from someone paraphrasing a source
instead of reading it.
