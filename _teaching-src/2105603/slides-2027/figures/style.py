"""Shared figure style for the 2027 decks: Teal-Amber palette, Source Sans 3 drawn as paths."""
from pathlib import Path
import base64, io, logging, re, tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from fontTools.ttLib import TTFont

logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
HERE = Path(__file__).resolve().parent
TEAL, AMBER, RUST, SKY, SAND = '#0F6E6B', '#E29A2D', '#BE654C', '#5A91BE', '#DFC98F'
INK, GRAPHITE, SLATE, MIST = '#1C242B', '#333F4A', '#66727C', '#B9C1C6'
FAMILY = 'Source Sans 3 ExtraLight'   # name of the embedded subset's default instance


def setup():
    scss = (HERE.parents[1] / 'theme/_fonts-embedded.scss').read_text()
    tmp = Path(tempfile.mkdtemp())
    pat = r'font-family:"Source Sans 3";\s*font-style:(\w+);\s*font-weight:(\d+);\s*src:url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)'
    for style, weight, data in re.findall(pat, scss):
        font = TTFont(io.BytesIO(base64.b64decode(data))); font.flavor = None
        path = tmp / f'SourceSans3-{weight}-{style}.ttf'; font.save(path)
        font_manager.fontManager.addfont(str(path))
    plt.rcParams.update({'svg.fonttype': 'path', 'font.family': FAMILY, 'font.size': 17,
                         'mathtext.fontset': 'custom', 'mathtext.rm': FAMILY, 'mathtext.it': FAMILY + ':italic',
                         'axes.edgecolor': GRAPHITE, 'axes.labelcolor': INK, 'xtick.color': GRAPHITE, 'ytick.color': GRAPHITE})


def tidy(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.grid(axis='y', color=MIST, lw=.6, alpha=.6)
