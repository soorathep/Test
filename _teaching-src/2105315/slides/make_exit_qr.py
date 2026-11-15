"""QR codes for the 2105315 exit-ticket form, one PNG per session (graphite on white, 600 dpi).

    python3 make_exit_qr.py 1 2 3      # writes figures/exit-qr-s01.png ...
"""
from pathlib import Path
import sys

import qrcode

URL = 'https://www.skhgroup.net/teaching/2105315/slides/exit.html?s={}'
out = Path(__file__).resolve().parent / 'figures'
out.mkdir(exist_ok=True)
for s in [int(a) for a in sys.argv[1:]] or [1]:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=22, border=4)
    qr.add_data(URL.format(s)); qr.make(fit=True)
    qr.make_image(fill_color='#333F4A', back_color='white').save(out / f'exit-qr-s{s:02d}.png', dpi=(600, 600))
    print(out / f'exit-qr-s{s:02d}.png')
