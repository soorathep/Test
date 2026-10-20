"""Rebuild the four-page supplemental Lab 01 guide with research Python."""
from pathlib import Path
import argparse
import os
import tempfile
from xml.sax.saxutils import escape

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'lab01-guide-matplotlib'))
import skh_palette as skh
skh.use()
from matplotlib.font_manager import findfont, FontProperties
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE='https://www.skhgroup.net/teaching/2105603/'
C={k:colors.HexColor(v) for k,v in skh.C.items()}
W,H=595.276,841.89
M=43
CW=W-2*M
for name,weight in [('Body','normal'),('Bold','bold')]:
    pdfmetrics.registerFont(TTFont(name,findfont(FontProperties(family='DejaVu Sans',weight=weight))))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
ST={
 'body':ParagraphStyle('body',fontName='Body',fontSize=10,leading=14.1,textColor=C['graphite']),
 'small':ParagraphStyle('small',fontName='Body',fontSize=8.5,leading=11.8,textColor=C['graphite']),
 'head':ParagraphStyle('head',fontName='Bold',fontSize=12,leading=16,textColor=C['teal']),
 'title':ParagraphStyle('title',fontName='Bold',fontSize=21,leading=26,textColor=C['teal']),
 'eq':ParagraphStyle('eq',fontName='Body',fontSize=10.2,leading=15.5,textColor=C['graphite']),
 'table':ParagraphStyle('table',fontName='Body',fontSize=8.5,leading=11.6,textColor=C['graphite']),
}
class Doc:
 def __init__(self,path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  self.c=canvas.Canvas(str(path),pagesize=(W,H),pageCompression=1,initialFontName='Body',invariant=1)
  self.c.setTitle('Week 1 Lab 01 walkthrough: Ideal VLE and TP flash')
  self.c.setAuthor('2105603 | SKH Research Group');self.n=0;self.y=0
 def page(self,title,kicker):
  if self.n:self.c.showPage()
  self.n+=1;self.c.setFillColor(C['teal']);self.c.rect(0,H-11,W,11,fill=1,stroke=0)
  self.c.setFont('Bold',8.4);self.c.drawString(M,H-35,'2105603  /  WEEK 01  /  LAB 01 WALKTHROUGH')
  self.c.setFillColor(C['graphite']);self.c.setFont('Body',7.5)
  self.c.drawString(M,27,'Advanced Chemical Engineering Thermodynamics | Supplemental classroom follow-up')
  self.c.drawRightString(W-M,27,f'{self.n} / 4')
  self.y=H-58;self.p(title,'title');self.p(kicker,'small',gap=11)
 def p(self,text,kind='body',gap=6,width=None,x=M):
  p=Paragraph(text,ST[kind]);_,h=p.wrap(width or CW,H)
  assert self.y-h>46,(self.n,text[:65],self.y,h)
  p.drawOn(self.c,x,self.y-h);self.y-=h+gap
 def head(self,text):self.p(text,'head',gap=6)
 def lines(self,n=1):
  self.c.setStrokeColor(C['mist']);self.c.setLineWidth(.45)
  for _ in range(n):
   self.y-=16;assert self.y>46;self.c.line(M,self.y,W-M,self.y)
  self.y-=7
 def table(self,rows,widths,padding=5):
  t=Table([[Paragraph(str(v),ST['table']) for v in row] for row in rows],colWidths=widths)
  t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Body'),('BACKGROUND',(0,0),(-1,0),C['paper']),('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.6,C['mist']),('INNERGRID',(0,0),(-1,-1),.4,C['mist']),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding)]))
  _,h=t.wrap(CW,H);assert self.y-h>46,(self.n,self.y,h)
  t.drawOn(self.c,M,self.y-h);self.y-=h+9
 def link(self,label,path):self.p(f'<link href="{escape(BASE+path)}" color="{skh.C["teal"]}"><u>{escape(label)}</u></link>','small')
 def finish(self):
  assert self.n==4;self.c.save();print(self.path)

def guide(path):
 d=Doc(path)
 d.page('Open, set up and predict','Guide page 1 | Video chapters 1-4 | Write your predictions before continuing past chapter 3.')
 d.link('Watch the Lab 01 demonstration from the beginning','lab01-video.html#chapter-1')
 d.link('Open Lab 01 in a second browser tab','labs/#experiment')
 d.p('This walkthrough supplements the completed Week 1 classroom lesson. It shows the ideal binary calculation and how to retain evidence. Work at your own pace; it is not a new three-hour assignment. No repeat exit-ticket or attendance submission is required. Keep page 4 closed until your independent attempt on page 3.','small')
 d.head('1. Select the defined teaching case')
 d.table([['Control','Enter or select'],['Chemical system','Teaching binary · synthetic'],['Liquid model','Ideal solution (the first entry)'],['Temperature / K','350'],['Flash pressure / kPa','95'],['Feed fraction z₁','0.5'],['Diagram','P-x-y · fixed temperature']],widths=[200,CW-200])
 d.p('The lab uses a <b>1 mol feed basis</b>. Component 1 is Component A and component 2 is Component B. Under <b>Data, models &amp; limits</b>, follow <b>Property records</b>: at 350 K, P₁<super>sat</super>=150 kPa and P₂<super>sat</super>=60 kPa. These are supplied synthetic definitions, not real-fluid measurements. Keep T fixed throughout this walkthrough.','small')
 d.p('Sliders update immediately. After typing, click <b>Calculate equilibrium →</b>. A changed-input message means the old result is not current. The page has several later-course model options; use only the ideal solution here.','small')
 d.head('2. Predict first: pause at chapter 3')
 d.p('At fixed T and z₁, how should the vapor fraction change when pressure decreases? Select your prediction in <b>At fixed T and feed composition, lowering P...</b>. Predict the phases at 95, 110 and 80 kPa.','small');d.lines(2)
 d.p('For an ideal binary at fixed T, calculate the two boundaries before checking the display:','small')
 d.p('P<sub>bubble</sub> = x₁P₁<super>sat</super> + (1−x₁)P₂<super>sat</super>, using x₁=z₁<br/>1/P<sub>dew</sub> = y₁/P₁<super>sat</super> + (1−y₁)/P₂<super>sat</super>, using y₁=z₁','eq');d.lines(1)
 d.p('The boundary outputs answer two separate first-phase questions. They do not say that both coexisting compositions at 95 kPa equal z₁. Continue at chapter 4 to compare your prediction with the displayed boundaries.','small')

 d.page('Calculate, check and compare pressures','Guide page 2 | Video chapters 5-11 | Save the 95 kPa baseline before changing only pressure.')
 d.head('3. Read the 95 kPa flash result')
 d.p('Click <b>Calculate equilibrium →</b>. Record the phase label, <b>Vapor fraction · β</b>, <b>Liquid · x₁</b> and <b>Vapor · y₁</b>. On the P-x-y diagram, a horizontal tie line joins liquid and vapor at the same pressure. The feed composition lies between them in a two-phase state.','small')
 d.table([['Case','P / kPa','Present phases','x₁','y₁','β'],['01A','95','<br/>','<br/>','<br/>','<br/>'],['01B','110','<br/>','<br/>','<br/>','<br/>'],['01C','80','<br/>','<br/>','<br/>','<br/>']],widths=[48,65,133,86,86,CW-418],padding=7)
 d.head('4. Verify a balance by hand')
 d.p('On the 1 mol basis, L=1−β and V=β (mol). Calculate x₂=1−x₁ and y₂=1−y₁. Check both component balances using the values you recorded:','small')
 d.p('z₁ = (1−β)x₁ + βy₁<br/>1−z₁ = (1−β)(1−x₁) + β(1−y₁)','eq');d.lines(2)
 d.p('Expand <b>Check the solution</b> to compare your residual with the reported balance. A small rounded hand residual is expected. It verifies this calculation, not real-property accuracy. For an absent phase, record “not present” instead of inventing its composition.','small')
 d.p('Chapter 7: select <b>Diagram → Rachford-Rice · vapor fraction</b>. Its zero determines β for the converged K values; the horizontal axis is vapor fraction, not composition. For this ideal example, Kᵢ=Pᵢ<super>sat</super>/P. Return to <b>P-x-y · fixed temperature</b> before saving.','small')
 d.head('5. Save each calculation before the next change')
 d.p('Open <b>Study workspace · reopen and compare cases</b> near the top. Set <b>Label for the next captured case</b> to “01A - 95 kPa”. Write a short interpretation in <b>Your explanation</b>, then click <b>Export experiment ↓</b> near the bottom. It downloads the JSON and adds the case to the in-memory comparison.','small')
 d.p('For 01B, change only <b>Flash pressure</b> to 110 kPa, calculate, record and export with its new label. For 01C, change only pressure to 80 kPa; repeat. Keep system, model, T and z₁ unchanged. Review the three recorded cases in Study workspace.','small')
 d.p('<b>Curve CSV ↓</b> downloads the selected diagram curve; it does not contain the complete study or restore controls. <b>Copy link to these conditions</b> shares settings, but omits prediction and reflection. Use the experiment JSON and comparison to retain full evidence.','small')

 d.page('Reopen and try a new pressure','Guide page 3 | Chapter 12: restore a saved case. Chapter 13: pause for your own 90 kPa attempt.')
 d.head('6. Download, load, restore, then recalculate')
 d.p('1. In <b>Study workspace · reopen and compare cases</b>, check that 01A, 01B and 01C are listed. Click <b>Download comparison</b> and keep the file <b>index-comparison.json</b> with this guide. The list is in memory; download it before leaving the page.','small')
 d.p('2. To verify your saved file, first confirm that the download exists. Then use <b>Clear comparison</b> to avoid duplicate cases. This clears the current list, not the downloaded file. The comparison holds up to eight cases.','small')
 d.p('3. Choose that file through <b>Load studies or a comparison JSON</b>. Click <b>Restore</b> beside the 95 kPa baseline. Verify the system, ideal model, T=350 K, P=95 kPa and z₁=0.5.','small')
 d.p('4. Click <b>Calculate equilibrium →</b> again. Compare the fresh result with your saved 01A values. Loading retains recorded evidence; restoring inputs is not itself a fresh equilibrium calculation.','small')
 d.p('<b>Raw JSON units:</b> inputs.P and workspace.controls.P keep the displayed kPa value (95), but result.P and boundary result pressures use Pa (95000 Pa=95 kPa). Temperature is K; compositions and β are dimensionless. Check field meaning and units before comparing numbers.','small')
 d.head('7. Independent attempt: pressure = 90 kPa')
 d.p('Keep the same synthetic system, ideal model, T=350 K and z₁=0.5. Pause at chapter 13 for about five minutes. Write your prediction and hand calculation before running the lab or opening page 4.','small')
 d.p('<b>A.</b> Compare 90 kPa with your bubble and dew boundaries. Which phases should be present?','small');d.lines(1)
 d.p('<b>B.</b> Use P=x₁P₁<super>sat</super>+(1−x₁)P₂<super>sat</super> to find x₁. Then find y₁=x₁P₁<super>sat</super>/P and β=(z₁−x₁)/(y₁−x₁). Calculate liquid and vapor amounts on the 1 mol basis.','small');d.lines(2)
 d.p('<b>C.</b> Check both component balances. Explain the direction of the change in β from 95 to 90 kPa.','small');d.lines(2)
 d.p('<b>D.</b> Now enter 90 kPa, calculate and compare. Save as “01D - 90 kPa practice” if you wish. Keep your first attempt and any correction. Continue to chapter 14 and page 4 only after the attempt.','small')

 d.page('Self-check after your attempt','Guide page 4 | Video chapter 14 | Compare methods and interpretation, not only the displayed digits.')
 d.head('Boundaries: two separate composition specifications')
 d.p('P<sub>bubble</sub>(x₁=0.5)=0.5(150)+0.5(60)=<b>105 kPa</b>.<br/>P<sub>dew</sub>(y₁=0.5)=1/[0.5/150+0.5/60]=<b>85.714286 kPa</b>.','eq')
 d.p('At this fixed feed composition, pressures between those boundaries give two phases. Above 105 kPa the feed is liquid; below 85.714286 kPa it is vapor. These statements apply to the specified synthetic ideal model at 350 K.','small')
 d.table([['Case','Present phases','x₁','y₁','β'],['95 kPa','Liquid + vapor','0.388889','0.614035','0.493506'],['110 kPa','Liquid only','0.500000','Not present','0'],['80 kPa','Vapor only','Not present','0.500000','1']],widths=[70,130,102,108,CW-410])
 d.p('At 95 kPa: x₁=(95−60)/(150−60)=0.3888889; y₁=x₁(150)/95=0.6140351; β=(0.5−x₁)/(y₁−x₁)=0.4935065. Thus L=0.5064935 mol and V=0.4935065 mol. Both balances give 0.500000 mol of each component, up to rounding.','small')
 d.p('At 110 kPa all feed is liquid (L=1, V=0 mol); at 80 kPa all is vapor (L=0, V=1 mol). An absent phase has no bulk composition to report. A zero phase amount is meaningful; a missing composition is not zero.','small')
 d.head('Your 90 kPa attempt')
 d.p('Since 85.714286 &lt; 90 &lt; 105 kPa, the result is liquid + vapor.','small')
 d.p('x₁=(90−60)/(150−60)=<b>1/3</b><br/>y₁=(1/3)(150/90)=<b>5/9</b><br/>β=(1/2−1/3)/(5/9−1/3)=<b>3/4=0.75</b>','eq')
 d.p('L=<b>0.25 mol</b>, V=<b>0.75 mol</b>. Component 1: (1/4)(1/3)+(3/4)(5/9)=1/12+5/12=<b>1/2 mol</b>. Component 2: (1/4)(2/3)+(3/4)(4/9)=1/6+1/3=<b>1/2 mol</b>.','small')
 d.p('Lowering P from 95 to 90 kPa increases β from 0.493506 to 0.75 at fixed T and z. The tie-line compositions change as well. Do not confuse x₁ or y₁ (composition within a phase) with β (the fraction of the total feed that is vapor).','small')
 d.head('Retain a short, reproducible explanation')
 d.p('Check that you have: (1) your prediction and first 90 kPa attempt; (2) a labeled three-pressure comparison; (3) one hand balance; (4) downloaded experiment/comparison JSON; and (5) a restored case recalculated to the same result. Write one model assumption and explain the pressure trend. Your files remain local unless you choose to share them.','small')
 d.p('Use this demonstration to complete or revisit the original Week 1 practice. No repeat exit-ticket or attendance submission is required.','small')
 d.link('Return to the Lab 01 video','lab01-video.html#chapter-14')
 d.finish()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('output/pdf/week01-lab-guide.pdf'))
 args=p.parse_args();guide(args.output)
