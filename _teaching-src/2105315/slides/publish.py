"""Copy a rendered deck from _site/ to teaching/2105315/slides/.

    quarto render s01.qmd && python3 publish.py
"""
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEST = REPO / 'teaching/2105315/slides'

for path in sorted((HERE / '_site').rglob('*')):
    if path.is_dir():
        continue
    target = DEST / path.relative_to(HERE / '_site')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    print(target.relative_to(REPO))

# Thai caption font (OFL), shared by every course at a fixed path.
fonts = REPO / 'teaching/shared/fonts'
fonts.mkdir(parents=True, exist_ok=True)
for name in ('Sarabun-Regular.ttf', 'LICENSE_SARABUN.txt'):
    shutil.copyfile(REPO / 'teaching/2105603/assets' / name, fonts / name)
