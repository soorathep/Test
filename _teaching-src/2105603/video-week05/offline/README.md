# Week 5 offline package and scoped release hashes

These are independent local proposal sources. They do not publish a website,
change an engine version, or operate on NFS storage. The previous Week 1–4
package remains the starting point. Do not execute the public-writing commands
until the coordinating agent confirms that final public staging is ready.

The new package includes the 32-slide Week 5 deck, the six-page worksheet,
two-page Lab guide, five-page worked solutions, study hub, and updated learning
path. Week 5 uses one worksheet and Lab 12. All video players and recorded media
remain outside the ZIP. Relative player links become live website URLs without
losing chapter fragments. The included slides are an alternative offline route,
not extra work. Session 5 submission still requires internet.

The three scripts require an absolute Python interpreter path. The builder and
validator use PyMuPDF already available in the research environment. They install
nothing. `--site` is always explicit; no checkout is inferred. Example commands
from the teaching project directory:

```sh
# Read-only proposal. The receipt stays in this task's local directory.
"$HOME/.venvs/research/bin/python" asynchronous-week05/offline/refresh-release-manifest.py \
  --site "$HOME/.codex/worktrees/week05-video/Test" \
  --receipt asynchronous-week05/offline/release-proposal.json

# After final staging is confirmed: update four public file hash entries only.
"$HOME/.venvs/research/bin/python" asynchronous-week05/offline/refresh-release-manifest.py \
  --site "$HOME/.codex/worktrees/week05-video/Test" \
  --apply --receipt asynchronous-week05/offline/release-update-qa.json

# Build and verify a local proposal archive. It leaves the public ZIP alone.
"$HOME/.venvs/research/bin/python" asynchronous-week05/offline/build-offline.py \
  --site "$HOME/.codex/worktrees/week05-video/Test" \
  --output "$HOME/Documents/Projects/Adv thermo/asynchronous-week05/offline/thermodynamics-offline.zip"
"$HOME/.venvs/research/bin/python" asynchronous-week05/offline/validate-offline.py \
  --site "$HOME/.codex/worktrees/week05-video/Test" \
  --archive "$HOME/Documents/Projects/Adv thermo/asynchronous-week05/offline/thermodynamics-offline.zip" \
  --output asynchronous-week05/offline/offline-qa.json
```

After approval to replace the public ZIP, omit `--output` from the builder and
`--archive` from the validator. The default archive is
`teaching/2105603/files/thermodynamics-offline.zip` inside the supplied checkout.
The scripts never commit, push, deploy, or change other public source files.

The release-hash script updates only these existing `files` entries:

- `learning-path.html`
- `assessments.html`
- `assets/learning-guide.js`
- `assets/learning-path.json`

It preserves every engine version, `sourceCommit`, `sourceState`, `sourceHashes`,
and all other public file entries. The separate receipt records the scoped
change and before/after SHA-256 values. It does not pretend that the old engine
source commit is a new course-content commit.

The archive validator checks CRC and every file against its own `MANIFEST.json`,
excludes media/private system files, compares PDFs byte for byte to staged
originals, checks their page counts, and verifies that HTML and learning-data
changes are limited to the documented offline rewrites. It checks Week 5 demo
anchors 20, 22, and 30 and retains Week 4 opening and Lab demo anchors. The public
Lab release manifest remains byte-identical inside the ZIP; the archive's own
manifest is authoritative for the rewritten offline learning-data URLs.

Source provenance and the prior builder's hash are recorded in
`LOCAL_PROVENANCE.json`. No archive base version is invented.
