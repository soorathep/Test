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

GitHub Pages builds with **Jekyll 3.10** plus a fixed plugin set, which differs from the
Jekyll documented on jekyllrb.com. Two traps have already broken a deploy:

- **`where_exp` accepts only ONE expression.** Writing `where_exp: "w", "w.a or w.b"` parses
  on Jekyll 4 but fails on Pages with *"Liquid syntax error: Expected end_of_string but found
  id"*, and the whole site stops deploying — no page updates at all until it is fixed. Filter
  inside the loop instead: a plain `if` tag does accept `or`. If a section needs to know
  whether it is empty, count matches with the `plus: 1` filter first.
- **Every `.md` file in the repo is rendered, front matter or not** — Pages enables the
  `jekyll-optional-front-matter` plugin. That includes guide files like this one. So never
  write a complete Liquid tag inside a guide: a brace-percent opener with its matching closer
  will be *executed*, not shown, and a bad example takes the build down with it. Describe the
  syntax in words, as above.

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
| Publication counts (322 / 7,085 / h-48) | yearly | `id="publications"` `<h2>` + note | Scopus |
| People and alumni placements | yearly | `id="people"` | Your records |
| Patents, awards, roles | rare | `id="recognition"`, home callout | CV |
| Instruments | rare | `id="facilities"` | MRBS instrument booking calendar |
| Activity photos | whenever | Home + `/activities/` | `_data/activities.yml` + `img/activities/` |
| **Blog posts** | **whenever** | **`_posts/*.md`** | **You** |
| Seminars and invited talks | a few / year | `/teaching/seminars/` catalog | `soorathep/seminars` for source and publication |

**The CV is upstream of the site.** When the CV changes, the site follows, never the
reverse. Anything on the site that is not traceable to the CV, Scopus, or a file from a
publisher should not be there.

---

## Recipes

### Add activity photos

Put the images in `img/activities/` and add an event at the top of
`_data/activities.yml`, following its template. The home page chooses an event at
random, then one photo from it, each time the page loads. New events join this
selection automatically. The caption uses the event title and date; it does not
identify the people in the photo. Portrait and landscape photos are shown in full.
Without JavaScript, the first photo of the newest nonempty album is displayed.

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

### Add a seminar

Standalone seminars and invited talks are authored and published in
[soorathep/seminars](https://github.com/soorathep/seminars), not in this repository.
This is separate from Seminar 3 (2105717), which remains in course-seminar3.

Follow the new repository README and its _teaching-src/seminars publishing
instructions. Keep public-profile safeguards for Conferences and ACSSI.
MMS3 retains its already-authorized published notes/script exception.

The main site keeps _data/seminars.yml and teaching/seminars/index.html as its
catalog; add new entries here only to keep that catalog synchronized with the
dedicated site. All material links point to the dedicated site. Do not regenerate
or restore duplicate seminar sources/assets in main_web.

Legacy HTML entry pages are small redirects preserving query strings and
fragments. Deleted direct PDF/ZIP/asset URLs return HTTP 404; the 404 page can
forward JavaScript-enabled browser navigation but is not an HTTP redirect and
does not preserve non-browser download clients or arbitrary embeds. Link directly
to https://soorathep.github.io/seminars/teaching/seminars/ for downloads.

The separate ACSSI book of abstracts under files/ and news image under img/news/
remain in main_web and must not be removed with the migrated seminar materials.

---

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
they will disagree. Refresh the "18 September 2026" date at the same time.

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

## Navigation menu (reorganised 24 Oct 2026)

The menu lives in ONE file: `_includes/nav.html`. Both `index.html` and
`_layouts/default.html` pull it in with `{% include nav.html %}`. Before this,
the two pages each kept their own copy and drifted (Join Us was missing on
every page except the home page).

Five groups, each a top link plus a dropdown, and a Join Us button:

- Research: Research programme, CTI Framework, Facilities
- People: Group members, Collaborators
- Publications: Publications, Recognition
- Teaching: Courses, Seminars, Resources
- News: Lab news, Essays, Activities

Rules:
- Add a new page as a dropdown item under an existing group. Do not add a
  sixth top-level item without a strong reason; five is the point.
- Home-page sections are linked as `{{ site.baseurl }}/#section`, never
  `index.html#section`, so clicking them on the home page only changes the
  hash (no reload).
- The script in nav.html highlights the group that contains the current
  page, handles the MENU button, and closes the dropdown after a click.
  index.html no longer touches the nav links; do not add nav code back there.
- On phones (<= 900 px) every group opens flat under MENU; no dropdowns.


## Course websites after 2026-11-15

The following public repositories are the authoritative publishing destinations for course updates:

| Course | Repository | Site |
| --- | --- | --- |
| 2105315 | https://github.com/soorathep/course-2105315 | https://soorathep.github.io/course-2105315/ |
| 2105603 | https://github.com/soorathep/course-2105603 | https://soorathep.github.io/course-2105603/ |
| 2105620 | https://github.com/soorathep/course-2105620 | https://soorathep.github.io/course-2105620/ |
| 2105623 | https://github.com/soorathep/course-2105623 | https://soorathep.github.io/course-2105623/ |
| 2105717 (Seminar 3) | https://github.com/soorathep/course-seminar3 | https://soorathep.github.io/course-seminar3/ |

The research site's teaching catalog links to the independent course sites. Existing teaching pages, worksheets, labs and video URLs in this repository remain online unchanged for compatibility. Do not remove them or redirect learner-state pages without a reviewed migration: worksheet answers and notes can live in browser localStorage on the original domain. Existing feedback forms also rely on the original authorized origin. New course updates belong in the course repositories, not in these legacy copies. Source/editor projects can keep their own repositories; their publication scripts must target the matching course repository rather than Test. Do not re-point a source project's Git remote blindly.

Annual archive policy: at the end of each teaching year, prepare a reviewed, versioned archive with checksums, confirm rights/license and remove student personal data. Publish to Zenodo only after owner review of the content and metadata, verify the DOI and downloadable files, then add an annual archive link. No Zenodo record was published by this migration.

The branch course-sites-migration-20261115 is an UNDEPLOYED experiment that excludes old video URLs. Do not merge it: it would break direct media embeds and non-browser download clients. Only the catalog-only migration was deployed.


### Legacy 2105717 Seminar 3 compatibility files

Authoritative teaching content is in [course-seminar3](https://github.com/soorathep/course-seminar3).
The verified October 2026 archive is https://doi.org/10.5281/zenodo.24248149.
Its ZIP SHA-256 is 452834573774caf9946711566a812325f821f3e4710aadec197fbe292cf399f3.

Duplicate Seminar 3 material and the old worksheet application were retired from
main_web on 15 November 2026 with the owner's explicit authorization. Thirteen
HTML entry pages remain as small redirects preserving query strings and fragments.
The main course catalog already routes to the dedicated site through
_data/course_migration.json; preserve that mapping.

Before retiring the old worksheet application, all four worksheet templates,
their render dependencies and the blank English workbook were exported as
2105717-worksheets-original-site-2026-10.zip, SHA-256
4412387a964c26b83c0e8c82473d81ba3136fd2129a7e43cffa658fc1cc49d83.
The full original templates and dependencies also remain in the verified Zenodo
archive and dedicated course repository. Browser-saved student answers are not
in the repository and are not included in these template exports.

Only six media compatibility files remain unchanged: both lecture MP4s plus their
two posters and two chapter lists. These preserve direct video URLs and existing
embeds. JavaScript 404 handling is not an HTTP redirect for media clients.
Do not remove these without a separately verified migration or explicit owner
decision addressing direct media access. This folder is not an active authoring
project; do not restore duplicate slides or libraries.


## Activities gallery after 16 November 2026

The authoritative gallery and new albums are maintained in https://github.com/soorathep/activities and published at https://soorathep.github.io/activities/. The old /activities/ entry redirects there.

Keep this repository's nine existing img/activities images and _data/activities.yml unchanged unless a separate compatibility migration is approved: the main homepage uses both for its random-photo feature and old direct image URLs must continue working. These are a curated legacy snapshot, not the authoring destination for new albums. New albums do not automatically appear on the main homepage; update that curated highlight deliberately when needed. The earlier Add activity photos instructions apply to the new repository for gallery additions, not to main_web.

The new gallery's initial nine images were verified byte-for-byte after deployment. Shared main-site CSS/layout and unrelated courses remain unchanged. No DNS or custom-domain changes were required.

## Live Activities feed (16 November 2026)

The homepage now fetches https://soorathep.github.io/activities/albums.json on every visit with cache revalidation, and randomly chooses from that current gallery. This supersedes the curated-snapshot limitation above. Add photos/albums only to the activities repository. No main_web edit is needed for new albums. Existing embedded metadata/images remain an immediate loading/offline/error fallback and preserve legacy image URLs. The remote photo is installed only after loading successfully; labels use textContent and photo URLs are constrained to the gallery image directory.
