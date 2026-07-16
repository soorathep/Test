# Maintaining skhgroup.net

```
index.html   the one-pager (~52 KB), plain static HTML
assets/style.css           all styling, shared by the one-pager and the blog
covers/                    journal cover art, 760 px wide
_data/covers.yml           the cover list — the page is generated from this
_data/people.yml           current lab members — the People page is generated from this
member_form.docx           the form you send to a new member
img/                       PI photo
news.html                  the blog index (served at /news/ , not /news.html)
404.html                   custom not-found page (permalink pinned — see the trap below)
og.png                     1200x630 link-preview card. Referenced by index.html's
                           og:image/twitter:image. If you rename or delete it, every
                           share on LINE, Slack, X, or Facebook shows a broken image.
robots.txt                 points crawlers at the sitemap
img/og/                    1200x630 landscape share cards, one per cover
tools/make_og_cards.py     regenerates them from _data/covers.yml
_posts/                    one markdown file per post   <- the part you edit often
_layouts/                  page shell for blog pages
_config.yml                Jekyll settings
```

Two halves, deliberately:

- **The one-pager** is hand-written HTML. It now carries `layout: null` front matter so
  Jekyll runs Liquid in it — that is what pulls the two latest posts onto the home page.
  Because of that, **never paste a literal `{{` or `{%` into index.html**; Jekyll will try
  to execute it and the build will fail.
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

1. Resize to **760 px wide, JPEG, quality ~84**. Publisher files are 2,500–6,000 px and have
   no place on a web page. Keep the originals in your own archive.
2. Name it `Journal_Name_YEAR.jpg` and upload it to `covers/`.
3. Add a block at the **top** of `_data/covers.yml`:
   ```yaml
   - file: Journal_Name_2027.jpg
     journal: Journal Name
     meta: Vol 15, No 3 · 12 March 2027 · Front cover
     year: 2027
     alt: Journal Name cover, March 2027
     title: The paper title, if the cover prints one   # omit this line if it does not
   ```

That is the whole job. The home strip, the Recognition gallery, the cover count, and the
year range in the heading all read from that file and update themselves. **Never type the
number of covers into the page.**

### Add or update a lab member

1. Send them **`member_form.docx`**. Seven fields, bilingual, about five minutes.
   They send it back with **one photo as a separate file**.
2. Put every returned form and photo into `inbox/` — any filenames, all mixed together.
3. Run it:
   ```bash
   pip install python-docx pyyaml pillow
   python tools/make_people.py
   ```
   It parses the forms, matches each photo to its form by name, crops every photo to a
   600 px square biased toward the upper third, writes `img/people/`, and rewrites
   `_data/people.yml`. It shows you a diff and asks before overwriting anything.
4. **Read the YAML before committing.** The script never invents a value: a field left
   blank comes out absent, not guessed.
5. Commit `_data/people.yml` and `img/people/`. The People page, the head-count, and the
   grid all follow.

Someone leaves: delete their entry from `_data/people.yml` and add them to the alumni
table in `index.html`. Someone's topic changes: edit the one line.

No script to hand? The YAML is a plain list — type the entry yourself and drop a square
JPEG in `img/people/`. The script is a convenience, not a dependency.

**Photos.** They will arrive at 4000 px, sideways, in five aspect ratios. Do not fight it;
the script fixes rotation from EXIF and crops square. The site renders them grayscale
until hover, which is what makes a set of mismatched phone snaps read as one group. A
member with no photo gets a neutral placeholder rather than a hole in the grid.

**Privacy.** The form asks for nothing you would not put on a poster: name, role, year,
one sentence of research, previous degree, an optional ORCID. No phone numbers, no home
addresses, no dates of birth, no nationality. Keep it that way — this is a public page and
several members are early-career people who did not choose to be searchable.

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

### Share a post to Facebook or LinkedIn

Every post page has **LinkedIn / Facebook / X / Copy link** buttons under the article.
Click one, or paste the post URL into a post on either platform. The preview card is
generated from the page's Open Graph tags.

**Never point `image:` at a file in `covers/`.** Journal covers are portrait (760x999).
Facebook and LinkedIn want 1.91:1 landscape, so a portrait cover gets centre-cropped into
a letterbox that cuts off the top and bottom of the artwork. Point at the pre-built
landscape card instead:

```yaml
image: /img/og/Batteries_and_Supercaps_2026.jpg   # 1200x630, cover + caption
```

Posts with no `image:` fall back to `og.png`, which is always a safe default.

**Making a card for a new cover.** Add the cover to `_data/covers.yml` first, then either
ask Claude for the card, or run it yourself:

```bash
pip install pillow pyyaml fonttools
python tools/make_og_cards.py     # reads _data/covers.yml, writes img/og/*.jpg
```

**If the preview looks wrong or stale**, the platform has cached the old tags. Force a
refresh:

- LinkedIn: <https://www.linkedin.com/post-inspector/>
- Facebook: <https://developers.facebook.com/tools/debug/>

Paste the URL, click Inspect / Scrape Again. LinkedIn caches for about 7 days and there is
no way around it other than the inspector, so **check the preview before you post**, not
after.

**A post does not have to be an essay.** Three sentences announcing a cover is a post.
The failure mode for an academic blog is not posts that are too short, it is a "Latest
news, March 2024" banner sitting on a 2026 site. Short and alive beats long and abandoned.

### Put an image in a post

1. **Resize to ~760 px wide first.** A phone photo is 4000 px and 5 MB; the page shows it
   at 760 px either way, so the other 4.3 MB is pure load time.
2. Upload it to `img/news/` (Add file → Upload files → drag). Lowercase, no spaces:
   `2026-08-glovebox.jpg`.
3. In the post:
   ```markdown
   ![Short description of the photo](/img/news/2026-08-glovebox.jpg)
   ```
   With a caption:
   ```html
   <figure>
     <img src="/img/news/2026-08-glovebox.jpg" alt="Short description">
     <figcaption>The caption readers actually see.</figcaption>
   </figure>
   ```

Paths start with `/` because `baseurl` is `""` and the site sits at the root of
www.skhgroup.net. `covers/` is for journal cover art only; put post photos in `img/news/`.

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

`404.html` pins `permalink: /404.html` for the same reason. GitHub Pages only serves a
custom 404 from that exact path; without the pin Jekyll would build it to `/404/` and you
would silently get GitHub's generic error page back.

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
