"""Embed a portable scientific-symbol fallback for the six session decks."""
import base64
from pathlib import Path
from matplotlib import font_manager
root=Path(__file__).resolve().parent.parent
font=Path(font_manager.findfont('DejaVu Sans'))
css='/* Embedded symbol fallback keeps scientific Unicode glyphs portable. */\n@font-face{font-family:"Thermo Symbols";src:url(data:font/ttf;base64,'+base64.b64encode(font.read_bytes()).decode()+') format("truetype");font-weight:100 900;font-style:normal;}\n.reveal p,.reveal li,.reveal td,.reveal th{font-family:"Source Sans 3","Thermo Symbols",sans-serif;}\n'
(root/'assets/postmidterm.css').write_text(css)
(root/'assets/LICENSE_DEJAVU.txt').write_text((font.parent/'LICENSE_DEJAVU').read_text())
