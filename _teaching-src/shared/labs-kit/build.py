"""Publish the shared lab kit to teaching/shared/labs-kit/ (one copy for every course).

Run from anywhere: python3 _teaching-src/shared/labs-kit/build.py
Course build scripts call publish() first, so building a course also refreshes the kit.
"""
from pathlib import Path
import shutil

SOURCE = Path(__file__).resolve().parent
REPOSITORY = SOURCE.parents[2]
DESTINATION = REPOSITORY / 'teaching/shared/labs-kit'
FILES = ['labs-base.css', 'palette.css', 'mode.js', 'submission.js']
# palette.css is generated from skh_palette; the 2105603 course pages keep their own copy.
PALETTE_TWIN = REPOSITORY / 'teaching/2105603/labs/assets/palette.css'


def publish():
    if PALETTE_TWIN.exists() and PALETTE_TWIN.read_bytes() != (SOURCE / 'palette.css').read_bytes():
        raise SystemExit(f'palette.css differs from {PALETTE_TWIN.relative_to(REPOSITORY)}; regenerate both from skh_palette.')
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(SOURCE / name, DESTINATION / name)
        print((DESTINATION / name).relative_to(REPOSITORY))


if __name__ == '__main__':
    publish()
