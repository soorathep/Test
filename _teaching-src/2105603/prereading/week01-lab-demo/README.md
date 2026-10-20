# Supplemental Week 1 Lab 01 guide

This four-page guide accompanies `lab01-video.html`, a demonstration added after the Week 1 classroom lesson. It is not a new three-hour assignment and requires no repeat exit-ticket or attendance submission.

Rebuild from the course workspace:

```sh
"$HOME/.venvs/research/bin/python" /path/to/site/_teaching-src/2105603/prereading/week01-lab-demo/build_lab01_guide.py --output output/pdf/week01-lab-guide.pdf
```

Copy the verified PDF to `teaching/2105603/files/week01-lab-guide.pdf`. Dependencies are ReportLab, Matplotlib (font discovery), and the installed `skh_palette` package. The generator imports the Teal-Amber Lab Palette; fonts are embedded DejaVu Sans. Four explicit page boundaries and vertical overflow assertions keep the guide reproducible. No student records are included.

Page mapping:

1. Video chapters 1-4: setup, property definitions and predictions.
2. Chapters 5-11: flash, hand balance, Rachford-Rice plot, save and compare 95/110/80 kPa.
3. Chapters 12-13: comparison download, reload, restore, recalculate, and independent 90 kPa attempt.
4. Chapter 14: separate self-check and retained evidence.

Numerical contract: synthetic ideal binary, 350 K, saturation pressures 150 and 60 kPa, overall mole fraction 0.5. Bubble pressure is 105 kPa at liquid x1=0.5; dew pressure is 85.7142857 kPa at vapor y1=0.5. These are separate boundary calculations. The 90 kPa practice yields x1=1/3, y1=5/9 and beta=3/4. Do not add nonideal-liquid, virial or adiabatic calculations to this introductory core.

QA: render all four pages using Poppler and visually inspect them, check links/page count/bounds with PyMuPDF or pypdf, verify all fonts embedded and no Type 3 fonts with pdffonts. The adjacent qa.json records the reviewed PDF hash. Video links are resolved during the parent publication QA.
