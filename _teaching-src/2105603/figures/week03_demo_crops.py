"""Crop actual Lab03 UI captures for legible slide illustrations.

Sources are unaltered CUA screenshots under images/week03-lab03/.
Only viewport regions are selected; plots, values and labels are not changed.
Run with the absolute research interpreter.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'images/week03-lab03'
CROPS = {
    'baseline-controls-crop': ('01-baseline-controls.png', (46, 69, 319, 355)),
    'baseline-area-crop': ('02-baseline-area.png', (350, 81, 1195, 570)),
    'baseline-local-crop': ('03-baseline-local.png', (350, 81, 1195, 570)),
    'cancel-local-crop': ('04-canceling-local.png', (350, 81, 1195, 570)),
    'local41-crop': ('07-localized41-plot.png', (350, 140, 1195, 505)),
    'local161-crop': ('08-localized161-plot.png', (350, 140, 1195, 505)),
    'fit-score-crop': ('10-clean-fit-scores.png', (775, 38, 1184, 193)),
    'fit-controls-crop': ('10-clean-fit-scores.png', (47, 330, 314, 516)),
}
for name, (source, box) in CROPS.items():
    image = Image.open(FOLDER / source)
    assert box[0] >= 0 and box[1] >= 0 and box[2] <= image.width and box[3] <= image.height
    image.crop(box).save(FOLDER / f'{name}.png')
    print(name)
