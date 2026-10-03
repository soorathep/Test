"""Build six original, three-page pre-class handouts. Run with research Python."""
from pathlib import Path
import argparse, sys
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content import READINGS
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib.font_manager import findfont, FontProperties
import skh_palette as skh
C={k:colors.HexColor(v) for k,v in skh.C.items()}
for name,weight in [('Reading','normal'),('ReadingBold','bold')]:
    pdfmetrics.registerFont(TTFont(name,findfont(FontProperties(family='DejaVu Sans',weight=weight))))
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT.parent/'output'/'pdf');args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
W,H=595.28,841.89; M=48; CW=W-2*M
styles={
 'body':ParagraphStyle('body',fontName='Reading',fontSize=10.5,leading=16,textColor=C['graphite']),
 'small':ParagraphStyle('small',fontName='Reading',fontSize=8.5,leading=12,textColor=C['graphite']),
 'heading':ParagraphStyle('heading',fontName='ReadingBold',fontSize=13,leading=18,textColor=C['teal']),
 'title':ParagraphStyle('title',fontName='ReadingBold',fontSize=23,leading=29,textColor=C['teal']),
 'equation':ParagraphStyle('equation',fontName='Reading',fontSize=10,leading=17,textColor=C['graphite']),
}

def para(text,y,kind='body',width=CW,x=M):
    p=Paragraph(escape(text),styles[kind]); _,height=p.wrap(width,H)
    assert y-height>55,(text[:60],y,height)
    p.drawOn(c,x,y-height)
    return y-height-10

def start(week,page,label):
    c.setFillColor(C['teal']);c.rect(0,H-13,W,13,fill=1,stroke=0)
    c.setFont('ReadingBold',9);c.drawString(M,H-42,f'2105603  /  BEFORE CLASS  /  WEEK {week:02d}')
    c.setFillColor(C['graphite']);c.setFont('Reading',8)
    c.drawString(M,31,'Advanced Chemical Engineering Thermodynamics')
    c.drawRightString(W-M,31,f'{page} / 3  ·  {label}')
    return H-69

for week,d in enumerate(READINGS,1):
    dest=args.output/f'preclass-week-{week:02d}.pdf';c=canvas.Canvas(str(dest),pagesize=(W,H),initialFontName="Reading")
    c.setTitle(f'Week {week}: {d["title"]}');c.setAuthor('2105603 teaching materials')
    y=start(week,1,'Concepts');y=para(d['title'],y,'title');y=para('Read and prepare: 15–20 minutes total. Bring tentative answers; uncertainty is useful for discussion.',y,'small')
    y=para(d['question'],y,'heading')
    for heading,body in d['concepts']:
        y=para(heading,y,'heading');y=para(body,y)
    for eq in d['equations']:y=para(eq,y,'equation')
    c.showPage();y=start(week,2,'Worked example');y=para('One example to reason through',y,'title')
    y=para('Synthetic teaching values. These numbers illustrate the assumptions; they are not measurements of a real material.',y,'small')
    y=para(d['example'],y)
    if d['figure']:
        img=Image(str(ROOT/'figures'/'generated'/f'preclass-{d["figure"]}.png'),width=CW,height=CW*3.5/7.2)
        img.drawOn(c,M,y-img.drawHeight);y-=img.drawHeight+15
    else:
        y=para('Keep three questions separate',y,'heading')
        for line in ['Convergence: did the numerical algorithm satisfy its stopping criterion?', 'Consistency: are the observations compatible with thermodynamic constraints under the selected assumptions?', 'Prediction: how well does the model describe observations excluded from fitting?']:
            y=para(line,y)
    y=para('Check and interpret',y,'heading');y=para(d['check'],y)
    c.showPage();y=start(week,3,'Preparation');y=para('Bring three short answers',y,'title')
    y=para('A sketch, a few numbers or one sentence is enough. Do this before opening the calculator; revise your prediction in class.',y)
    for i,q in enumerate(d['prompts'],1):
        y=para(f'{i}. {q}',y)
        c.setStrokeColor(C['mist']);c.setLineWidth(.6)
        for _ in range(2):c.line(M,y-10,W-M,y-10);y-=20
        y-=10
    y=para('Optional extension',y,'heading');y=para(d['optional'],y,'small')
    url='https://www.skhgroup.net/teaching/2105603/labs/'+('' if d['lab']=='index' else d['lab']+'.html')
    y=para('Continue in the core lab',y,'heading');c.linkURL(url,(M,y-16,W-M,y+5),relative=0,thickness=0)
    y=para(url,y,'small')
    y=para('Reading locator: supplied textbook contents, sections '+d['book']+'.',y,'small')
    y=para('Original course explanation and examples, not a reproduction of the textbook. Section numbers are based on the supplied contents pages. Required weekly independent work: 15–20 minutes preparation plus 30–40 minutes follow-up; optional extensions are additional.',y,'small')
    c.save();print(dest)
