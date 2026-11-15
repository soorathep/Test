# Shared lab kit

One copy of the pieces every course's interactive labs use. Source lives here;
`build.py` publishes it to `teaching/shared/labs-kit/`, where pages load it.

| File | What it holds |
|---|---|
| `labs-base.css` | Tokens, page layout, controls, tables, study save/open, student-detail fields, the view switch, concept questions, phone-width figure scrolling. Imports `palette.css` and the Source Sans/Serif fonts. |
| `palette.css` | Teal-Amber Lab Palette v1.0 as CSS variables. Generated from `skh_palette`; `build.py` stops if it differs from `teaching/2105603/labs/assets/palette.css`. |
| `submission.js` | Student details (ids `student-first-name`, `student-last-name`, `student-id`), the study file name, JSON and CSV downloads, reading a reopened study. Each course passes its own `storeKey`. |
| `mode.js` | Core / second-view switch and the write-before-compare gate (30 characters). Exports `initLabs`, `currentMode`, `applyMode`. |
| `tests/smoke_test.py` | Playwright smoke test: main calculation, starter cases, second-view runs, concept gate, study download and reopen with student details (pages that have them), no JavaScript errors, no overflow at 375 px. |

## Using the kit in a course

1. Course stylesheet, first line: `@import url("/teaching/shared/labs-kit/labs-base.css");`, then only course rules.
2. Course `assets/mode.js`:

   ```js
   import { initLabs } from '/teaching/shared/labs-kit/mode.js';
   export { currentMode, applyMode } from '/teaching/shared/labs-kit/mode.js';
   initLabs({ storageKey: 'skh-<course>-mode' });
   ```

   Each course needs its own `storageKey`, so a student's view choice in one course does not carry into another.
   The second view is `graduate` internally (URL `?mode=graduate`, classes `.grad-only`, `.graduate-section`).
   Label it in the course HTML, for example "Graduate investigation" or "Extension".
3. Course build script: call this kit's `publish()` first (see `_teaching-src/2105603/labs-next/build.py`).
4. Course smoke test: a short wrapper that passes the published folder and lab list to `tests/smoke_test.py`
   (see `_teaching-src/2105603/labs-next/tests/smoke_test.py`).

2105315 uses `submission.js`. The 2105603 labs still use their own `student.js`, which writes the same student
block and file name; switching them to `submission.js` is a separate change to all 13 of those labs.

## Changing the kit

A change here affects every course. After editing, rebuild and run the smoke test of every course that uses the kit.
Paths are absolute (`/teaching/shared/...`) because the site is served at the domain root (`baseurl: ""`).
