# Guide: Updating the People page

Everyone on the People page — current members and alumni — comes from **one file**:
`_data/people.yml`. You never edit HTML. One entry per person. The page builds
all three groups from the fields on each entry:

| Field on the entry | Where the person appears |
|---|---|
| `status: current` | **Current members** card grid |
| `phd: <year>` | **Doctoral graduates** card grid |
| `postdoc: <period>` | **Postdoctoral alumni** card grid |

A person can be in more than one group at once. Someone who did a PhD here and
then a postdoc here has both `phd:` and `postdoc:` on their single entry and
shows up in both alumni grids automatically — no duplication.

---

## Add a new student (one person) — edit by hand

The simplest path for a single person.

**1.** Open `_data/people.yml`.

**2.** Copy the `Example Person` block from the bottom of the file, paste it
under the `# ── Current members ──` header, and fill it in. Delete any line you
do not have a value for.

```yaml
- name: Nina Somchai
  status: current
  role: PhD student
  since: 2025
  topic: Solid electrolytes for sodium batteries.
  photo: nina-somchai.jpg
  link: https://orcid.org/0000-0001-2345-6789
```

Leave out `phd`, `thesis`, `postdoc`, `now` — those are for alumni only.

**3.** Photo (optional). A square JPEG in `img/people/`, named to match the
`photo:` line. No photo? Delete the `photo:` line and a grey placeholder shows.

**4.** GitHub Desktop → Commit → Push. Wait 1–2 minutes, hard-refresh
(**Cmd + Shift + R**). The card appears under "Current members."

### Field reference

| Field | Required | Notes |
|---|---|---|
| `name` | yes | No "Dr." — the role line carries the title. |
| `status` | yes | `current` for a student/postdoc now in the lab. |
| `role` | — | e.g. "PhD student", "MEng student", "Postdoctoral researcher". |
| `since` | — | Year they joined. |
| `topic` | — | One sentence, plain English, no acronyms. |
| `photo` | — | Square JPEG in `img/people/`. Omit → placeholder. |
| `link` | — | ORCID or Google Scholar URL. |

---

## Add several people at once — form + script

Better when a whole intake arrives together.

**1.** Send `member_form.docx` to the new members.

**2.** Collect the returned forms **and** one photo each. Drop every file —
forms and photos, any filenames — into a folder called `inbox/` at the top of
the repo. (`inbox/` is git-ignored; it never gets committed.)

**3.** Run the script:

```bash
cd ~/Documents/GitHub/Test
pip install python-docx pyyaml pillow
python tools/make_people.py
```

**4.** It crops each photo to a square, adds the people to `people.yml` as
current members, shows you a diff, and asks before writing. Type `y`.
It **never removes alumni** — it only adds or updates current members.

**5.** Read the YAML, then Commit → Push.

---

## When a student graduates (current → alumni)

Do **not** create a new entry. Edit their existing one:

1. Change `status: current` → `status: alumnus`.
2. Add `phd: 2027` and a `thesis:` line.
3. Delete the current-only lines (`role`, `since`, `topic`).
4. If they leave for another institution, add `now: University X, Country`.
   If they stay at Chulalongkorn, omit `now`.

```yaml
# before
- name: Nina Somchai
  status: current
  role: PhD student
  since: 2025
  topic: Solid electrolytes for sodium batteries.
  photo: nina-somchai.jpg
  link: https://orcid.org/0000-0001-2345-6789

# after
- name: Nina Somchai
  status: alumnus
  phd: 2029
  thesis: Solid electrolytes for high-energy sodium batteries
  now: Chiang Mai University, Thailand      # omit this line if still at Chulalongkorn
  photo: nina-somchai.jpg
  link: https://orcid.org/0000-0001-2345-6789
```

They move from "Current members" to "Doctoral graduates" automatically.

## When a graduate starts a postdoc here

Add one line to their existing alumni entry — do not duplicate them:

```yaml
  postdoc: "2029–2031"
```

They now appear in **both** the Doctoral graduates and Postdoctoral alumni
grids from the same entry. (If they are actively in the lab again, you can also
set `status: current` and add back `role`/`since`/`topic` — they will then show
in all relevant groups at once.)

## When an alumnus changes jobs

Add or update the `now:` line on their entry. That's the whole edit.

---

## Photos

- Square JPEG, saved in `img/people/`, filename matching the entry's `photo:`.
- The site shows every photo greyscale until hover, so mismatched phone snaps
  still look like one set.
- The `make_people.py` script crops photos to a square automatically. Hand-added
  photos should be roughly square — anything wildly off will look cropped.
- No photo yet? Omit the `photo:` line. A placeholder shows; add the real photo
  later.

---

## Common mistakes

**Person does not appear at all**
→ Check `status:`. Only `current` shows in Current members. Alumni need `phd:`
or `postdoc:` to land in an alumni grid.

**Two cards for the same person**
→ You created a second entry instead of adding a field to the existing one.
Merge them into one entry — one person is always one entry.

**Card shows in the wrong group**
→ It follows the fields, not the section the entry sits in. `phd:` sends them to
Doctoral graduates wherever the entry physically is in the file.

**YAML won't build**
→ Indentation must be two spaces, and every `- name:` starts a new entry. If a
value contains a colon (`:`), wrap it in quotes: `topic: "Batteries: a review"`.

**Running `make_people.py` reformatted the file**
→ Expected. The script regenerates the comments and grouping every run. Your
data (including hand-edited alumni) is preserved; only layout is normalized.
