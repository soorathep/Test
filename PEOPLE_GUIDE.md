# Guide: Updating the People page

Everyone on the People page — current members and alumni — comes from **one file**:
`_data/people.yml`. You never edit HTML. One entry per person.

The page has **two blocks**, each split into **three levels**:

```
CURRENT MEMBERS
  Postdoctoral researchers
  Doctoral students   (D.Eng.)
  Master's students   (M.Eng.)

ALUMNI
  Postdoctoral researchers
  Doctoral graduates  (D.Eng.)
  Master's graduates  (M.Eng.)
```

A sub-group with nobody in it simply does not appear. Add the first person and it shows up.

## How each person is placed

| On the entry | Where they appear |
|---|---|
| `status: current` + `level: postdoc` | Current · Postdoctoral researchers |
| `status: current` + `level: deng` | Current · Doctoral students (D.Eng.) |
| `status: current` + `level: meng` | Current · Master's students (M.Eng.) |
| `postdoc: <period>` (and `status: alumnus`) | Alumni · Postdoctoral researchers |
| `deng: <year>` | Alumni · Doctoral graduates (D.Eng.) |
| `meng: <year>` | Alumni · Master's graduates (M.Eng.) |

**Current members** are placed by `level`. **Alumni** are placed by their degree
markers (`deng`, `meng`, `postdoc`). A person can carry more than one marker and
appear in more than one alumni group from a single entry — e.g. someone who earned
a D.Eng. here and then did a postdoc here shows in both.

---

## Add a new student or postdoc (current) — edit by hand

**1.** Open `_data/people.yml`.

**2.** Copy the `Example Person` block from the bottom, paste it under the
`# ── Current members ──` header, and fill it in. Delete lines you do not need.

```yaml
- name: Sutham Eeamtak
  status: current
  level: meng                 # postdoc | deng | meng — which current group
  role: Master's student      # free-text label shown on the card
  since: 2025
  topic: Zinc-ion battery electrolytes.   # optional, one sentence
  photo: sutham-eeamtak.jpg
  link: https://orcid.org/0000-0000-0000-0000
```

Leave out `deng`, `meng`, `thesis`, `postdoc`, `now` — those are for alumni.

**3.** Photo (optional). A square JPEG in `img/people/`, named to match `photo:`.
No photo? Delete the `photo:` line and a grey placeholder shows.

**4.** GitHub Desktop → Commit → Push. Wait 1–2 minutes, hard-refresh
(**Cmd + Shift + R**).

### Field reference

| Field | Used by | Notes |
|---|---|---|
| `name` | all | No "Dr." — the role line carries the level. |
| `status` | all | `current` or `alumnus`. |
| `level` | current | `postdoc` \| `deng` \| `meng`. Decides the current sub-group. |
| `role` | current | Free text, e.g. "Doctoral student", "Postdoctoral researcher". |
| `since` | current | Year they joined. |
| `topic` | current | One sentence, plain English, no acronyms. |
| `deng` | alumni | Year the D.Eng. was earned here. |
| `meng` | alumni | Year the M.Eng. was earned here. |
| `thesis` | alumni | Thesis title. `Na<sub>0.44</sub>MnO<sub>2</sub>` renders. |
| `postdoc` | alumni | Postdoc period here, e.g. `"2022–2026"`. |
| `now` | alumni | Where they are now. Omit if still at Chulalongkorn. |
| `photo` | all | Square JPEG in `img/people/`. Omit → placeholder. |
| `link` | all | ORCID or Google Scholar URL. |

---

## Add several people at once — form + script

Better when a whole intake arrives together.

**1.** Send `member_form.docx` to the new members.

**2.** Collect the returned forms **and** one photo each. Drop every file into a
folder called `inbox/` at the top of the repo. (`inbox/` is git-ignored.)

**3.** Run the script:

```bash
cd ~/Documents/GitHub/Test
pip install python-docx pyyaml pillow
python tools/make_people.py
```

**4.** It crops each photo, reads each form's **Role** to set the `level`
(Postdoc → `postdoc`, PhD/D.Eng. → `deng`, MEng/Master → `meng`), adds the people
as current members, shows a diff, and asks before writing. Type `y`.
It **never removes alumni** — it only adds or updates current members. If a role
is unusual and the level can't be guessed, it prints a warning; set `level:` by hand.

**5.** Read the YAML, then Commit → Push.

---

## When a student graduates (current → alumni)

Edit their existing entry — do **not** create a new one:

1. Change `status: current` → `status: alumnus`.
2. Add the degree year: `deng: 2029` (doctoral) or `meng: 2027` (master's), and a
   `thesis:` line.
3. Delete the current-only lines (`level`, `role`, `since`, `topic`).
4. If they leave for another institution, add `now: University X, Country`. If they
   stay at Chulalongkorn, omit `now`.

```yaml
# before
- name: Sutham Eeamtak
  status: current
  level: meng
  role: Master's student
  since: 2025
  photo: sutham-eeamtak.jpg

# after
- name: Sutham Eeamtak
  status: alumnus
  meng: 2027
  thesis: Electrolyte additives for aqueous zinc-ion batteries
  now: PTT Research, Thailand     # omit if still at Chulalongkorn
  photo: sutham-eeamtak.jpg
```

They move from Current · Master's students to Alumni · Master's graduates automatically.

## When a graduate starts a postdoc here

If they are actively in the lab again, set `status: current` and `level: postdoc`,
and add `role`/`since`. Keep their `deng:`/`meng:` markers. They then show in
Current · Postdoctoral researchers **and** in the matching alumni graduate group.

If the postdoc has finished, set `status: alumnus` and add `postdoc: "2029–2031"`.

## When an alumnus changes jobs

Add or update the `now:` line on their entry. That's the whole edit.

---

## Photos

- Square JPEG, saved in `img/people/`, filename matching the entry's `photo:`.
- The site shows every photo greyscale until hover, so mismatched phone snaps still
  look like one set.
- `make_people.py` crops photos to a square automatically. Hand-added photos should
  be roughly square.
- No photo yet? Omit the `photo:` line. A placeholder shows; add the real photo later.

---

## Common mistakes

**Person does not appear at all**
→ Current member missing `level`, or alumnus missing every degree marker
(`deng` / `meng` / `postdoc`). Placement follows those fields.

**Current member in the wrong group**
→ Check `level` (`postdoc` / `deng` / `meng`), not `role` (which is only a label).

**Two cards for the same person**
→ You created a second entry instead of adding a field to the existing one.
One person is always one entry.

**Alumnus shows in "current" or vice-versa**
→ Check `status`. Current uses `level`; alumni use the degree markers.

**YAML won't build**
→ Two-space indentation; every `- name:` starts a new entry. If a value contains a
colon, wrap it in quotes: `topic: "Batteries: a review"`.

**Running `make_people.py` reformatted the file**
→ Expected. The script regenerates comments and grouping every run. Your data,
including hand-edited alumni, is preserved; only layout is normalized.
