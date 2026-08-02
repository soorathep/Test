# Lab Figure Palette — AI Prompt Pack

Paste the block below into ChatGPT, Claude, Gemini, or any coding assistant **before**
you ask it to make a plot, figure, diagram, or scheme. It makes the AI use the
laboratory's **Teal–Amber palette** correctly — the same colours, in the same order,
with the same meanings — so every figure looks like it came from this group and stays
readable for colour-blind readers and in greyscale.

> Works for matplotlib / seaborn / plotly / R-ggplot code, for schematic diagrams,
> and for image-generation prompts. Copy from `====` to `====`.

---

```
====  LAB FIGURE PALETTE — follow exactly  ====

You are producing a scientific figure for our laboratory. Use ONLY the palette below.
Do not invent colours, do not use matplotlib/Excel defaults, never use a rainbow/jet
colormap, and never use a red–green pair.

CATEGORICAL COLOURS — use strictly in this order (the order is accessibility-optimised):
  1 teal     #0F6E6B   control / baseline / untreated / reference
  2 amber    #E29A2D   the effect of interest (treatment, mutant, the main result)
  3 rust     #BE654C   third condition
  4 skyblue  #5A91BE   fourth condition
  5 sage     #83A462   fifth condition
  6 plum     #995A90   sixth condition
  7 graphite #333F4A   (also a neutral) extra category only if unavoidable
  8 sand     #DFC98F   fills / confidence bands / shaded regions
For N groups use the first N colours. Never pick from the middle of the list.

NEUTRALS — all non-data ink (never pure black):
  ink      #1C242B   body text, titles, labels
  graphite #333F4A   axes, ticks, tick labels, reference/threshold lines
  slate    #66727C   secondary text, captions, annotations
  mist     #B9C1C6   gridlines, minor rules
  paper    #F3F0EB   panel backgrounds, table banding

SEQUENTIAL RAMP (unsigned magnitude: intensity, density, abundance, probability) —
low value light, high value dark:
  #EDF9FA #B8E4E7 #85CED2 #51B7BC #009FA3 #00888A #006F70 #005756 #003F3D

DIVERGING RAMP (signed quantity with a real zero: log2FC, z-score, difference) —
teal = negative, paper = zero, amber = positive; ALWAYS centre on zero (vmin = -vmax):
  #007372 #008C8B #53A6A5 #86C0BF #B6D9D9 #F3F0EB #ECCF9F #DDAD68 #CC8C36 #BA6A00 #A84500

RULES:
  - Reserve amber for the effect of interest; teal is the default/control.
  - Categorical colours for discrete groups ONLY; ramps for continuous data ONLY.
  - Axes/ticks/reference lines in graphite (#333F4A), text in ink (#1C242B). No pure black.
  - Gridlines in mist (#B9C1C6), thin. Drop top and right spines.
  - Line width >= 1.5 pt, marker size >= 4 pt. Keep alpha >= 0.6.
  - If more than 4 groups, add a redundant channel: marker shape, line style, or direct labels.
  - Export vector (PDF/SVG/EPS) when possible; otherwise PNG at >= 600 dpi.
  - Single column = 85 mm wide, double column = 180 mm.

If you output code, apply these as the colour cycle / colormap and axis style, and
briefly note which colour maps to which condition.

====  END PALETTE  ====
```

---

## Ready-made follow-up requests

After pasting the block above, ask for what you need, e.g.:

- *"Make a grouped bar chart of capacity for control vs treated vs third condition, with error bars, following the lab palette."*
- *"Plot these three cycling curves; label them control/treated/additive and use the palette."*
- *"Heatmap of this matrix using the sequential teal ramp, with a colourbar."*
- *"Diverging heatmap of log2 fold-change centred on zero using the diverging ramp."*
- *"Redraw this figure to fix the rainbow colormap and red–green pair using our palette."*

## If you already use Python

You usually don't need this prompt — use the module directly:

```python
import labpalette as lp
lp.apply()                      # house style: colours, fonts, 600 dpi
ax.plot(x, y, label="control")  # cycles teal, amber, rust, ...
ax.imshow(Z, cmap=lp.cmap("teal"))
ax.imshow(D, cmap=lp.cmap("diverging"), vmin=-3, vmax=3)
```

## Full specification

The complete rationale, accessibility validation, and per-tool setup (R, Illustrator,
LaTeX, CSS) are in **lab_palette_guide.pdf**. The one-page swatch card is
**lab_palette_sheet.pdf** — print it and pin it up.
