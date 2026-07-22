# Guide: Adding a New Paper (Enhanced Design)

This guide walks through creating a striking new paper announcement with the **V2 design system** — scientific + vibrant aesthetics.

---

## 1. OG Card (Social Media Preview)

### Generate Enhanced OG Cards

The new `make_og_cards_v2.py` script creates **scientific-looking, vibrant cards** perfect for announcements.

```bash
cd ~/Documents/GitHub/Test
pip install pillow pyyaml fonttools
python tools/make_og_cards_v2.py
```

**Features:**
- ✓ Cyan accent bar (scientific framing)
- ✓ "NEW PAPER" badge
- ✓ Vibrant top bar
- ✓ Better typography hierarchy
- ✓ Larger, striking journal name

**Output:** `img/og/Journal_Name_YEAR.jpg` (1200×630, optimized)

---

## 2. Create a New Paper Post

### Step 1: Add Cover to `_data/covers.yml`

First, prepare your journal cover (760 px wide, JPEG ~84 quality):

```yaml
- file: Journal_Name_2026.jpg
  journal: Journal Name (Full Name)
  meta: Vol 15, No 3 · 15 September 2026 · Front cover
  year: 2026
  alt: Journal Name cover, September 2026
  title: Paper title as it appears on the cover
```

Upload the cover to `covers/` folder.

### Step 2: Create New Blog Post

Use the **new V2 post layout** for striking presentation.

**File:** `_posts/2026-09-15-paper-title.md`

```markdown
---
title: "Paper title here"
date: 2026-09-15
description: "One sentence: what the paper does and why it matters."
kind: paper
tag: Paper
research_domain: "Zinc-ion batteries · Interface engineering"
image: /covers/Journal_Name_2026.jpg
layout: post_v2
---

## Opening paragraph

Engaging summary of the research. Why should anyone care? What problem does this solve?

## Key findings

- Finding 1 with context
- Finding 2 with implications
- Finding 3 with broader impact

### With images

![Your caption]({{ site.baseurl }}/img/news/2026-09-figure.jpg)

## Full paper

Read the complete paper: [DOI 10.xxxx/xxxxx](https://doi.org/10.xxxx/xxxxx)

**Authors:** ...

**Acknowledgments:** ...
```

### Step 3: Commit & Push

```bash
git add _posts/2026-09-15-paper-title.md
git add covers/Journal_Name_2026.jpg
git add _data/covers.yml
git commit -m "Add new paper: Journal Name 2026"
git push origin main
```

---

## 3. Update OG Card (if needed)

After adding the cover, regenerate OG cards:

```bash
python tools/make_og_cards_v2.py
git add img/og/Journal_Name_2026.jpg
git commit -m "Generate OG card for Journal Name 2026"
git push origin main
```

---

## Post Template Features (V2)

### Featured Image
```markdown
image: /covers/Journal_Name_2026.jpg
```
This appears at the top of the post for immediate visual impact.

### Research Domain
```markdown
research_domain: "Zinc-ion batteries · Interface engineering"
```
Appears as a highlighted sidebar showing the research focus.

### Description (Lede)
```markdown
description: "One-line summary shown in social previews and post index."
```

### Enhanced Styling
- Better spacing and typography hierarchy
- Scientific color accents (Prussian + Sodium)
- Larger featured images
- Better mobile responsiveness

---

## Example: Complete Paper Post

```markdown
---
title: "Why ionic conductivity does not predict durability: design rules for sodium batteries"
date: 2026-09-15
description: "Six design rules and failure-mode logic for sodium batteries across liquid and solid electrolytes."
kind: paper
tag: Paper
research_domain: "Sodium-ion · Solid electrolytes · Coordination–Transport–Interface"
image: /covers/Journal_of_Materials_Chemistry_A_2026.jpg
layout: post_v2
---

## Abstract

Ionic conductivity is widely reported but poorly predicts cell lifetime in sodium batteries. We propose six falsifiable design rules derived from the Coordination–Transport–Interface framework.

## Methodology

Operando XAS + XRD on cycling cells, paired with stack-pressure disclosure.

## Key Results

### Design Rule 1: First-shell anion fraction drives stability
Not transference number alone.

### Design Rule 2: Stack-pressure changes the sulfide-over-oxide ranking
Under matched pressure baseline, the usual advantage inverts.

## Full Paper

**Weldegebrieal G.K., Tangthuam P., Choi M.Y., Lin J., Yonezawa T., Praserthdam S., Kheawhom S.**

*Journal of Materials Chemistry A* · [DOI 10.1039/D6TA01969B](https://doi.org/10.1039/D6TA01969B)
```

---

## Design Philosophy

✓ **Scientific:** Professional, peer-reviewed aesthetic  
✓ **Vibrant:** Striking colors (Cyan + Sodium + Prussian)  
✓ **Visual:** Images + metadata + hierarchy  
✓ **Scannable:** Hierarchy makes key findings quick to spot  

The V2 system makes papers feel like **research highlights**, not blog posts.

---

## Troubleshooting

**OG card looks wrong on LinkedIn/Facebook?**
→ Use the inspector to force-refresh:
- LinkedIn: https://www.linkedin.com/post-inspector/
- Facebook: https://developers.facebook.com/tools/debug/

**Post layout not updating?**
→ Make sure front matter has `layout: post_v2` (not `post`)

**Featured image not showing?**
→ Check path starts with `/` (e.g., `/covers/...`)
