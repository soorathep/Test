# Maintaining skhgroup.net

The site is one static HTML file plus two image folders. No build step, no framework,
no dependencies. If you can edit a text file, you can update this site.

```
skhgroup_redesign_1.html   the whole page (~61 KB)
covers/                    journal cover art, 760 px wide
img/                       PI photo
```

Everything is in `skhgroup_redesign_1.html`: eight sections (`<div class="page" id="...">`),
one `<style>` block at the top. Content is plain HTML, not generated.

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

### Update the publication counts

One `<h2>` and one `<div class="note">` in `id="publications"`. Change both together or
they will disagree. Refresh the "July 2026" date at the same time.

---

## Deploying

Commit to `github.com/soorathep/Test`. GitHub Pages redeploys on push. If images do not
appear, the folder is missing or misnamed: paths are case-sensitive and relative to the
HTML file.

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
