"""Copy a rendered 2027 deck to teaching/2105603/slides-2027/ and use the vendored KaTeX.

    quarto render s01.qmd && python3 publish.py
"""
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
DEST = HERE.parents[2] / 'teaching/2105603/slides-2027'
CDN = re.compile(r'https://cdn\.jsdelivr\.net/npm/katex@[^/"]+/dist/')

for path in (HERE / '_site').rglob('*'):
    if path.is_dir():
        continue
    target = DEST / path.relative_to(HERE / '_site')
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == '.html':
        target.write_text(CDN.sub('../site_libs/katex/', path.read_text()))
    else:
        shutil.copyfile(path, target)
    print(target.relative_to(HERE.parents[2]))
