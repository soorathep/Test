"""Rebuild the four English Week 3 handouts using research Python.

Run with --output <directory>; --only-background preserves the old six-week
prereading build entry point. This script contains the complete teaching text.
"""
from pathlib import Path
import argparse
import os
import tempfile
from xml.sax.saxutils import escape

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'week03-matplotlib'))
import skh_palette as skh
skh.use()
from matplotlib.font_manager import findfont, FontProperties
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode

BASE='https://www.skhgroup.net/teaching/2105603/'
EXIT='https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=3'
NIST='https://trc.nist.gov/TDE/Help/TDE103b_v4_0/VLE-DataSets-ConsistencyTests/'
C={k:colors.HexColor(v) for k,v in skh.C.items()}
W,H=595.276,841.89
M=43
CW=W-2*M
for name,weight in [('Body','normal'),('Bold','bold')]:
    pdfmetrics.registerFont(TTFont(name,findfont(FontProperties(family='DejaVu Sans',weight=weight))))
pdfmetrics.registerFontFamily('Body', normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
ST={
 'body':ParagraphStyle('body',fontName='Body',fontSize=10,leading=14.3,textColor=C['graphite']),
 'small':ParagraphStyle('small',fontName='Body',fontSize=8.5,leading=11.8,textColor=C['graphite']),
 'head':ParagraphStyle('head',fontName='Bold',fontSize=12,leading=16,textColor=C['teal']),
 'title':ParagraphStyle('title',fontName='Bold',fontSize=22,leading=27,textColor=C['teal']),
 'eq':ParagraphStyle('eq',fontName='Body',fontSize=10.5,leading=16,textColor=C['graphite']),
 'table':ParagraphStyle('table',fontName='Body',fontSize=8.6,leading=12,textColor=C['graphite']),
}

class Doc:
 def __init__(self,path,title,pages,label):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  self.c=canvas.Canvas(str(path),pagesize=(W,H),pageCompression=1,initialFontName='Body')
  self.c.setTitle(title);self.c.setAuthor('2105603 | SKH Research Group')
  self.pages=pages;self.label=label;self.n=0;self.y=0
 def page(self,title,kicker):
  if self.n:self.c.showPage()
  self.n+=1;self.c.setFillColor(C['teal']);self.c.rect(0,H-11,W,11,fill=1,stroke=0)
  self.c.setFont('Bold',8.4);self.c.drawString(M,H-35,'2105603  /  WEEK 03  /  '+self.label.upper())
  self.c.setFillColor(C['graphite']);self.c.setFont('Body',7.5)
  self.c.drawString(M,27,'Advanced Chemical Engineering Thermodynamics | Independent holiday lesson')
  self.c.drawRightString(W-M,27,f'{self.n} / {self.pages}')
  self.y=H-59;self.p(title,'title');self.p(kicker,'small',gap=12)
 def p(self,text,kind='body',gap=6,width=None,x=M):
  # Paragraph markup is deliberate for equations, emphasis and clickable links.
  p=Paragraph(text,ST[kind]);_,h=p.wrap(width or CW,H)
  assert self.y-h>46, (self.path.name,self.n,text[:75],self.y,h)
  p.drawOn(self.c,x,self.y-h);self.y-=h+gap
 def head(self,text):self.p(text,'head',gap=7)
 def lines(self,n=1):
  self.c.setStrokeColor(C['mist']);self.c.setLineWidth(.45)
  for _ in range(n):
   self.y-=16;assert self.y>46
   self.c.line(M,self.y,W-M,self.y)
  self.y-=7
 def table(self,rows,widths=None,minh=None,padding=6):
  rows=[[Paragraph(str(v),ST['table']) for v in row] for row in rows]
  t=Table(rows,colWidths=widths or [CW/len(rows[0])]*len(rows[0]),rowHeights=minh)
  t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Body'),('BACKGROUND',(0,0),(-1,0),C['paper']),('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.6,C['mist']),('INNERGRID',(0,0),(-1,-1),.4,C['mist']),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding)]))
  _,h=t.wrap(CW,H);assert self.y-h>46,(self.path.name,self.n,self.y,h)
  t.drawOn(self.c,M,self.y-h);self.y-=h+10
 def link(self,label,path):self.p(f'<link href="{escape(BASE+path)}" color="{skh.C["teal"]}"><u>{escape(label)}</u></link>','small')
 def finish(self):
  assert self.n==self.pages,(self.path,self.n,self.pages)
  self.c.save();print(self.path)

def q(doc,label,text,n=1):
 doc.p(f'<b>{label}</b> {text}')
 if n:doc.lines(n)

def qr(doc):
 top=doc.y
 code=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,border=4,box_size=1)
 code.add_data(EXIT);code.make(fit=True);matrix=code.get_matrix();size=94
 cell=size/len(matrix);doc.c.setFillColor(C['graphite'])
 for row,values in enumerate(matrix):
  for col,value in enumerate(values):
   if value:doc.c.rect(M+col*cell,top-(row+1)*cell,cell,cell,stroke=0,fill=1)
 doc.p('<b>Session 3 exit ticket + feedback</b>','small',width=CW-111,x=M+111)
 doc.p('Scan the QR or use the clickable link below. The form is anonymous. It is not an attendance-identification form.','small',width=CW-111,x=M+111)
 doc.p(f'<link href="{escape(EXIT)}" color="{skh.C["teal"]}"><u>Open the Session 3 form</u></link>','small',width=CW-111,x=M+111)
 doc.y=min(doc.y,top-size-7)

def practice(output):
 d=Doc(output/'week03-practice.pdf','Week 3 practice: Consistency before LLE',6,'Practice record')
 d.page('Build and test your reasoning','Page 1 | A: 0-15 min. B: 15-40 min. Keep original attempts and add corrections separately.')
 d.p('Start at <link href="'+BASE+'week03-study.html"><u>week03-study.html</u></link>. Follow the English video and its pauses. Plan about 180 minutes including calculations, Labs 03/04, reflection and a 10-minute break. Timing is guidance, not a requirement to wait. Write here or in a notebook using the same labels. Background reading is optional.','small')
 d.head('A. Retrieve the VLE ideas')
 q(d,'A1.','Define x₁, y₁, z₁ and γ₁. Distinguish liquid composition from liquid activity a₁.')
 q(d,'A2.','Use γ₁=y₁P/(x₁P₁<super>sat</super>), with y₁=0.704857144627, P=158.707198211 kPa, x₁=0.50 and P₁<super>sat</super>=150 kPa. Compare with exp(0.399813). State the vapor and pressure-correction assumptions.')
 q(d,'A3.','A model fits the data closely. State what this establishes and one question it does not settle.')
 d.head('B. Connect the equation to the experimental path')
 q(d,'B1.','At fixed T and P, differentiate g=x ln γ₁+(1-x)ln γ₂ using the product rule. Identify the term removed by x d ln γ₁+(1-x)d ln γ₂=0. Show why dg/dx=ln(γ₁/γ₂). Here g means gᴱ/(RT).',2)
 d.p('<b>B2.</b> Complete the table before checking guide page 1. Name a required correction or assumption, not simply a test name.','small')
 d.table([['Path / available information','Local diagnostic: correction or limitation'],['Fixed T and P, composition varies','<br/>'],['Isothermal VLE, equilibrium P varies','<br/>'],['Real isobaric VLE, no independent hᴱ','<br/>']],widths=[225,CW-225])
 q(d,'B3.','Explain the difference between “not applicable,” “not assessed” and “outside this criterion.” May the first two be counted as passed?',1)
 d.p('<b>Output:</b> one derivation, a path table and your corrected A answers. Next: calculations on page 2.','small')

 d.page('Calculate global and local evidence','Page 2 | C: 40-65 min. Use a calculator or spreadsheet; show substituted values and units or dimensionless labels.')
 d.head('C1-C3. Area calculation')
 d.table([['x₁','0','0.25','0.50','0.75','1'],['L=ln(γ₁/γ₂)','2','1','0','-1','-2']],widths=[149,72,72,72,72,CW-437])
 d.p('<b>C1.</b> Compute all four trapezoids, positive area, signed negative area and signed sum S. <b>C2.</b> Add 0.20 to every L and recalculate S. <b>C3.</b> Explain why a small integral cannot certify every observation. These synthetic endpoint limits are supplied analytically. S is not normalized D.','small')
 d.lines(2)
 d.head('C4. Follow the worked local calculation')
 d.table([['x','ln γ₁','ln γ₂','g=x ln γ₁+(1-x)ln γ₂'],['0.40','0.72','0.32',''],['0.50','0.50','0.50',''],['0.60','0.32','0.72','']],widths=[65,100,100,CW-265])
 d.p('At x=0.50, calculate L=ln γ₁-ln γ₂ and r≈[g(0.60)-g(0.40)]/0.20-L(0.50). Then change <b>only ln γ₁ at x=0.60 from 0.32 to 0.36</b> and repeat. Follow the worked explanation; retain the clean and changed values.','small')
 d.lines(1)
 d.head('C5. Your independent local calculation')
 d.table([['x','ln γ₁','ln γ₂','g'],['0.30','0.735','0.135',''],['0.40','0.540','0.240',''],['0.50','0.375','0.375','']],widths=[65,100,100,CW-265])
 d.p('Calculate r at x=0.40 using the same <b>g-first</b> procedure. Repeat after changing <b>only ln γ₂ at x=0.50 from 0.375 to 0.425</b>. Show the two slopes and residuals before opening the check.','small')
 d.lines(1)
 d.p('<b>C6.</b> Both local tables are synthetic fixed-T,P examples with uniform spacing. Why can spacing, rounding and noise change a finite-difference result? Why is this one-point r not the Lab 03 score 100 mean |r|?','small')
 d.lines(1)

 d.page('Predict, run, compare and explain','Page 3 | D/E: 65-95 min. Guide pages 2-3. After this block, take the 95-105 min break.')
 d.link('Open Lab 03: Consistency tests','labs/consistency.html#consistency-experiment')
 d.p('<b>D1.</b> Follow the real baseline demonstration, then reproduce <b>Synthetic · isothermal, 350 K / Consistent reference / 41 points</b>. Inspect area and local charts; record and save the reference. Do not fit yet.','small')
 d.p('<b>D2-D3: predict BEFORE changing the control or viewing a check.</b> For canceling errors and a localized defect, predict which diagnostic may notice the discrepancy and why. An uncertain prediction is acceptable; preserve it.','small')
 d.table([['Case','Your prediction and reason'],['D2. Canceling, amplitude 0.25','<br/>'],['D3. Localized, amplitude 0.25','<br/>']],widths=[179,CW-179])
 d.p('Now run <b>D2: Canceling errors · zero net area</b> and <b>D3: Localized defect near x₁ = 0.35</b>, both at amplitude 0.25 / 41 points. <b>D4:</b> keep the localized defect and change only sampling to <b>161 points</b>. Record actual statuses, including unexpected ones.','small')
 d.table([['Run','Area D (%) / status','Local score / status','Residual shape / peak location'],['D1. Clean / 41','<br/>','<br/>','<br/>'],['D2. Canceling / 41','<br/>','<br/>','<br/>'],['D3. Localized / 41','<br/>','<br/>','<br/>'],['D4. Localized / 161','<br/>','<br/>','<br/>']],widths=[117,124,124,CW-365])
 d.p('<b>D5.</b> Return to Consistent reference / 41 points. Run <b>Run modeling test →</b> once; record Δp in % and Δy in percentage points. Explain why a close fit is not a general consistency certificate and why Herington is not applicable to this path.','small')
 d.lines(1)
 d.p('<b>E1.</b> Save or sketch a local-residual plot. Annotate the axes, case, amplitude, sample count and important peak or oscillation. Compare D3/D4: distinguish a numerical sampling change from new experimental evidence.','small')
 d.p('<b>E2.</b> Write 3-4 sentences: claim, numerical/chart evidence, and one assumption or limitation. Revisit both predictions and explain any correction. Use a separate page if needed.','small')
 d.lines(2)
 d.p('<b>Keep:</b> comparison table, annotated plot, explanation and separate exports for clean, canceling, localized-41 and localized-161. Save the clean fit before changing inputs. Export is local, not submission.','small')

 d.page('Predict liquid stability before calculating','Page 4 | F/G: 105-155 min. Complete F and G1 here before recording the Lab results on page 5.')
 d.head('F. Candidate equilibrium, stable equilibrium and amounts')
 q(d,'F1.','A solver finds equal chemical potentials. What additional global condition is needed for stable equilibrium? State the fixed conditions and material-balance constraint.',2)
 q(d,'F2.','For a supplied supported tie line with xᵅ=0.20 and xᵝ=0.80, calculate fβ=(z₁-xᵅ)/(xᵝ-xᵅ) and fα=1-fβ for z₁=0.50 and 0.35. Verify both component-1 balances. These hand endpoints are not Lab 04 outputs.',3)
 q(d,'F3.','Explain why positive curvature at the feed, or a line that touches twice, does not alone prove global stability.',2)
 d.head('G1. Three predictions, one fixed model')
 d.p('During the <b>3-minute pause on slide 34</b>, use <b>Margules · 1 parameter, A=3</b> to predict each homogeneous-feed state and equilibrium phase count. Write your reason or uncertainty <b>before watching the Lab 04 demonstration or opening a named preset</b>; both reveal the results.')
 d.table([['z₁','Predicted homogeneous feed','Predicted equilibrium / reason'],['0.02','<br/><br/>','<br/><br/>'],['0.12','<br/><br/>','<br/><br/>'],['0.50','<br/><br/>','<br/><br/>']],widths=[49,181,CW-230])
 d.p('A homogeneous-feed label concerns a hypothetical single liquid. The final equilibrium may have a different phase count. The model represents fixed hypothetical conditions, with no T/P controls.','small')
 d.p('<b>Next:</b> watch the complete Lab 04 screen demonstration on <b>slide 35</b>. Then use the <b>25-minute pause on slide 36</b> to rerun G2-G4 independently with Lab 04 and guide page 4. Preserve your predictions; do not replace them with demonstrated labels.','small')

 d.page('Test stability and close the balances','Page 5 | Slide 36: 25-minute independent rerun. Continue F/G to minute 155. Use guide page 4.')
 d.link('Open Lab 04: Liquid stability and LLE','labs/stability.html#lle-experiment')
 d.p('<b>G2.</b> After the demonstration, independently run A=3 at z₁=0.02, 0.12 and 0.50. For each run record the homogeneous-feed label separately from the final phase count, curvature sign and Gibbs-energy decrease / RT. For a one-liquid result, report its composition and mark coexistence fractions not applicable.','small')
 d.table([['z₁','Feed label / curvature sign','Final phase count / energy decrease','Actual xᵅ, xᵝ and fβ (if two liquids)'],['0.02','<br/><br/>','<br/><br/>','<br/><br/>'],['0.12','<br/><br/>','<br/><br/>','<br/><br/>'],['0.50','<br/><br/>','<br/><br/>','<br/><br/>']],widths=[42,140,145,CW-327])
 q(d,'G3.','Using the actual Lab endpoints, independently calculate fβ, fα and fαxᵅ+fβxᵝ for z₁=0.12 and 0.50. Show substituted numbers. Why is applying these two endpoints to z₁=0.02 infeasible?',3)
 d.p('<b>G4. Energy and global support.</b> Define m(x)=Δg<sub>mix</sub>/(RT)=x ln x+(1-x)ln(1-x)+3x(1-x). At z₁=0.12, calculate m(z₁), m<sub>split</sub>=fαm(xᵅ)+fβm(xᵝ), and m(z₁)-m<sub>split</sub>. Use your calculated fractions and Lab endpoints. This m includes ideal mixing; C used excess energy g only.','small')
 d.lines(3)
 d.p('Annotate a sketch or screenshot of the supporting tangent: mark xᵅ, xᵝ and z₁=0.12. Explain how positive local curvature can coexist with a lower-energy finite split. Check distinct endpoints, chemical-potential agreement and global support in <b>Verify the equilibrium</b>. Compare predictions with observations.','small')
 d.p('<b>Keep:</b> the three-case table, two balances, energy calculation, annotated tangent and explanations. Save each run with <b>Export study JSON</b>, naming z002, z012 and z050.','small')
 d.p('<b>Optional, only if time remains in this block:</b> at z₁=0.50 compare A=1.8, 2 and 3. This changes the model, unlike changing the feed. No A sweep, NRTL comparison, LLE fit or VLLE task is required.','small')

 d.page('Transfer, correct and reflect','Page 6 | H: 155-170 min. I: 170-180 min. Attempt all unseen cases before viewing their solutions.')
 d.head('H. Use the ideas on new cases')
 q(d,'H1.','Synthetic fixed-T,P data give g(0.20)=0.32, g(0.30)=0.42, g(0.40)=0.48 and L(0.30)=0.75, where g=gᴱ/(RT). Calculate the central slope and r at 0.30. Does one r determine a full-range consistency verdict?',1)
 q(d,'H2.','A real isobaric dataset gives a raw local score of 8.4, but independent hᴱ is unavailable. Should the local method be recorded as failed, passed or not assessed? Explain.',1)
 q(d,'H3.','Candidate coexistence endpoints are 0.15 and 0.75; z₁=0.39. Calculate both liquid fractions and the balance. What further evidence would establish that this candidate is stable?',2)
 q(d,'H4.','A hypothetical full-range isothermal assessment reports D=1.2%, local score=8.4, Δp=0.3% and Δy=0.2 percentage points. Use the Lab teaching criteria to classify each available test. Explain why a single overall “passed” label is misleading.',2)
 d.link('After attempting H1-H4: open worked solutions','files/week03-solutions.pdf')
 d.p('Compare, correct in a different color and retain your first answers. Keep the residual, average score and fitting errors distinct.','small')
 d.head('I. Exit ticket, feedback and saved evidence')
 d.p('<b>170-180 min:</b> use the existing Session 3 form during the pause on slide 43. Answer its LLE <b>concept</b> question using your three-state investigation. In the <b>evidence</b> answer include your Lab 03 area/local comparison, settings, numerical results and one limitation.','small')
 d.p('Complete feedback, including <b>actual study minutes and any pacing difficulty</b> in the existing feedback text. Submit once; wait for <b>Response received</b>. On slide 44, verify the receipt and save the record, corrections and Lab files/screenshots. Do not resubmit. The form is anonymous, not an individual attendance record. Lab exports and this worksheet do not submit themselves.','small')
 qr(d)
 d.finish()

def solutions(output):
 d=Doc(output/'week03-solutions.pdf','Week 3 worked solutions: Calculations and evidence',4,'Worked solutions')
 d.page('A-B. Connect properties and constraints','Solutions page 1 | Check after attempting. All hand tables and assessment cases are synthetic teaching data.')
 d.head('A. Retrieval and assumptions')
 d.p('<b>A1.</b> x₁: liquid mole fraction; y₁: vapor mole fraction; z₁: overall mole fraction. γ₁ is the liquid activity coefficient on the chosen pure-liquid standard state; activity a₁=γ₁x₁.')
 d.p('<b>A2.</b> γ₁=(0.704857144627×158.707198211)/(0.50×150)=<b>1.49154537</b>. exp(0.399813)=1.49154575; the small difference is rounding. The inference assumes ideal vapor, negligible Poynting correction and valid saturation-pressure correlations.')
 d.p('<b>A3.</b> A small residual establishes reproduction by the selected model under its property assumptions. It does not establish thermodynamic consistency at all compositions or predictive accuracy on independent observations.')
 d.head('B1. The product-rule bridge')
 d.p('g=x ln γ₁+(1-x)ln γ₂','eq')
 d.p('dg/dx = ln γ₁-ln γ₂ + x d ln γ₁/dx + (1-x)d ln γ₂/dx','eq')
 d.p('At fixed T and P, Gibbs-Duhem makes the last two terms sum to zero. Thus <b>dg/dx=L=ln(γ₁/γ₂)</b>. Both coefficient functions are constrained together; a single isolated γ value cannot test this composition-dependent identity.')
 d.head('B2-B3. The path determines what can be assessed')
 d.table([['Situation','Consequence'],['Fixed T and P','dg/dx=L; a finite-difference residual is approximate.'],['Isothermal VLE with varying P','Teaching diagnostic neglects vᴱ/(RT) dP. The temperature term is zero.'],['Real isobaric VLE without independent hᴱ','No corrected local verdict without independent hᴱ. Record not assessed.']],widths=[181,CW-181])
 d.p('General path: Σxᵢ d ln γᵢ = -hᴱ dT/(RT²) + vᴱ dP/(RT). Here hᴱ and vᴱ are molar excess properties. Isothermal does not automatically mean isobaric.','small')
 d.p('<b>Not applicable:</b> method does not match the path. <b>Not assessed:</b> information/correction is missing or disabled. <b>Outside this criterion:</b> an applicable evaluated diagnostic is outside its stated threshold. The first two are neither successful tests nor failures of the observations.')
 d.head('C1-C3. Signed area, not normalized D')
 d.table([['Interval','Baseline trapezoid','After uniform +0.20'],['0-0.25','0.375','0.425'],['0.25-0.50','0.125','0.175'],['0.50-0.75','-0.125','-0.075'],['0.75-1.00','-0.375','-0.325'],['Signed sum S','0','0.200']],widths=[135,170,CW-305],padding=3)
 d.p('Baseline positive area=0.5; signed negative area=-0.5. Endpoint limits were supplied. D=100|A-B|/(A+B), with nonnegative area magnitudes A/B, differs from signed S and is undefined when A+B vanishes. Opposing local errors can cancel.','small')

 d.page('C-D. A numerical residual is evidence','Solutions page 2 | Use the g-first operator throughout: form g, difference g, then subtract L at the center.')
 d.head('C4. Worked table at x=0.50')
 d.p('Clean g values: 0.40(0.72)+0.60(0.32)=<b>0.48</b>; g(0.50)=<b>0.50</b>; g(0.60)=<b>0.48</b>. L(0.50)=0.50-0.50=<b>0</b>. Central slope=(0.48-0.48)/0.20=<b>0</b>, so r=<b>0</b>.')
 d.p('Changed upper value: g(0.60)=0.60(0.36)+0.40(0.72)=<b>0.504</b>. The center L remains zero. Slope=(0.504-0.480)/0.20=<b>0.120</b>; r=<b>+0.120</b>. Use the composition weight 0.60 when propagating the changed log coefficient.')
 d.head('C5. Independent table at x=0.40')
 d.p('Clean g values are <b>0.315, 0.360, 0.375</b>. Slope=(0.375-0.315)/0.20=<b>0.300</b>; center L=0.540-0.240=<b>0.300</b>, so r=<b>0</b> apart from floating-point roundoff.')
 d.p('After changing upper ln γ₂ to 0.425, g(0.50)=0.50(0.375)+0.50(0.425)=<b>0.400</b>. Slope=(0.400-0.315)/0.20=<b>0.425</b>; r=0.425-0.300=<b>+0.125</b>. The center values have not changed.')
 d.p('<b>C6.</b> These uniform-grid derivatives are approximations. Differencing magnifies noise and depends on spacing and rounding; narrower spacing need not help noisy measurements. One local r is not 100 mean |r| across all interior points, and a three-point table supplies no full-range area verdict. Do not apply a dataset-average threshold to a single hand residual.','small')
 d.head('D1-D4. Actual Lab 03 reference values')
 d.table([['Synthetic isothermal run','D (%)','Local score','Result'],['Clean / 41','0.078692','0.117763','Both meet'],['Canceling / 41 / 0.25','0.073552','15.598698','Area meets; local outside'],['Localized / 41 / 0.25','2.013463','1.671839','Both meet; peak remains'],['Localized / 161 / 0.25','1.941724','1.565607','Both meet; inspect peak']],widths=[175,72,83,CW-330])
 d.p('Criteria: D&lt;5%; 100 mean |r|&lt;5. The local score is not a probability or percentage of faulty observations. Clean numerical scores are small rather than identically zero because integration/differentiation is discrete.','small')
 d.p('<b>D2:</b> the perturbation f=0.25 cos(2πx) has zero full-range integral. Adding (1-x)f to ln γ₁ and -xf to ln γ₂ leaves their weighted g unchanged but changes L by f. The continuous residual changes by -f. <b>D3-D4:</b> a narrow defect remains visible although both aggregate criteria are met. Sampling alters numerical representation; it adds no experimental measurements.','small')
 d.p('<b>D5:</b> at clean / 41, Δp≈1.12×10⁻⁶% and Δy≈6.48×10⁻⁷ percentage points. Near-zero reproduction is expected because NRTL is also the generator family. Herington is not applicable to this isothermal path. A failed fit supplies no modeling verdict.','small')

 d.p('<b>Optional D5 reopen:</b> use <b>Study workspace · reopen and compare cases</b>, load the exported JSON, then select <b>Restore</b> beside the case. Check its inputs and rerun <b>Run modeling test →</b>. The imported comparison preserves recorded evidence; it does not replace a current fit.','small')

 d.page('E-G. Evidence for a stable split','Solutions page 3 | Distinguish a homogeneous-feed classification from the final equilibrium state.')
 d.p('<b>E1-E2.</b> An acceptable record identifies axes, case, amplitude, resolution, a visible oscillation/peak, both scores and a limitation. Example: “At 350 K, 41 points and canceling amplitude 0.25, D=0.07355% meets the area criterion while the local score 15.5987 is outside 5. The oscillating residual shows what the integral conceals. This inference assumes ideal vapor and neglected pressure corrections; derivatives also depend on sampling.”','small')
 d.head('F1-F3. Global support and the hand lever rule')
 d.p('Equal chemical potentials or equal slopes identify a candidate. Stable equilibrium minimizes total Gibbs energy among admissible states at fixed T,P and material balance. Distinct endpoints and a common tangent supporting the whole admitted curve are required. Positive local curvature cannot alone establish the global minimum.')
 d.p('For supplied endpoints 0.20/0.80: z=0.50 gives fβ=fα=0.50; z=0.35 gives fβ=0.25,fα=0.75. Balances: 0.50(0.20)+0.50(0.80)=0.50 and 0.75(0.20)+0.25(0.80)=0.35. These are not Lab 04 endpoints.','small')
 d.head('G1-G2. Three feeds, one-parameter Margules A=3')
 d.table([['z₁','Homogeneous feed / curvature','Equilibrium','Energy decrease / RT'],['0.02','Stable / +45.0204','One liquid at x₁=0.02','0'],['0.12','Metastable / +3.4697','Two liquids','0.00821636'],['0.50','Unstable / -2.0000','Two liquids','0.11519417']],widths=[46,182,143,CW-371])
 d.p('For the two-liquid runs, xᵅ=<b>0.07072018</b> and xᵝ=<b>0.92927982</b>. They stay fixed when only z changes. At z=0.02, those coexistence endpoints are not a feasible split for that feed: the formal fβ≈-0.059076 is negative. Report one liquid, not two liquids with a negative amount.','small')
 d.head('G3. Independent fractions and balances')
 d.p('At z=0.12: fβ=(0.12-0.07072018)/(0.92927982-0.07072018)=<b>0.05739825</b>; fα=<b>0.94260175</b>. Balance: 0.94260175(0.07072018)+0.05739825(0.92927982)≈<b>0.12000000</b>. At z=0.50 both fractions are 0.50 and the balance is 0.50.')
 d.head('G4. The metastable feed can lower its energy')
 d.p('Using m(x)=x ln x+(1-x)ln(1-x)+3x(1-x), m(0.12)=<b>-0.05012499</b>. At both endpoints m≈<b>-0.05834135</b>, so the weighted split has this same energy. The decrease is <b>0.00821636</b> per RT. Positive curvature at 0.12 gives local resistance to infinitesimal changes, but a finite split lowers total Gibbs energy.')
 d.p('The supporting line describes realizable mixtures only between its endpoints. Extending it to z=0.02 violates nonnegative amounts. For actual coexistence, combine the balance, distinct endpoints, chemical-potential agreement and global tangent evidence. The Lab does not predict nucleation barriers or separation rates.','small')

 d.page('H-I. Transfer checks and reflection','Solutions page 4 | Do not read this page until you have attempted all H questions.')
 d.head('H1. One new residual')
 d.p('Central slope=[g(0.40)-g(0.20)]/(0.40-0.20)=(0.48-0.32)/0.20=<b>0.80</b>. Subtract L(0.30)=0.75 to obtain <b>r=+0.05</b>. This is a single approximate point residual, not the average across a dataset and not evidence about missing endpoint intervals.')
 d.head('H2. Missing isobaric information')
 d.p('Record <b>not assessed</b> for the heat-corrected local consistency test. Independent hᴱ is required for hᴱ/(RT²)dT/dx. A raw score of 8.4 cannot be treated as an applicable failed local criterion when that required correction is unavailable. The number can still be shown as an uncorrected diagnostic.')
 d.head('H3. New endpoints and feed')
 d.p('fβ=(0.39-0.15)/(0.75-0.15)=<b>0.40</b>; fα=<b>0.60</b>. The balance is 0.60(0.15)+0.40(0.75)=<b>0.39</b>. Nonnegative amounts and a correct balance make the split feasible, not necessarily stable.')
 d.p('Confirm distinct phases, chemical-potential/common-tangent conditions and a tangent supporting the entire admitted Gibbs-energy curve. The candidate must be the global minimum subject to the balance at the specified T,P. Endpoints supplied without this evidence are only candidates.')
 d.head('H4. Three numerical results, no universal badge')
 d.table([['Diagnostic','Given result','Interpretation under its assumptions'],['Isothermal area','D=1.2%','Meets D<5%'],['Local average','Score=8.4','Outside score<5'],['Selected model','Δp=0.3%; Δy=0.2 pp','Both reproduction criteria met']],widths=[137,155,CW-292])
 d.p('A close fit does not cancel a local discrepancy; the diagnostics ask different questions. State the disagreement and inspect its location and assumptions. Herington remains not applicable to the hypothetical isothermal path. None of these numbers alone identifies the cause as measurement error.')
 d.head('I. A useful anonymous reflection')
 d.p('In the Session 3 concept answer, explain the LLE evidence, especially the distinction between metastable homogeneous feed and stable two-liquid equilibrium. In the evidence answer, give a reproducible Lab 03 case and explain the area/local comparison, including the sampling limitation. During the slide 43 pause, complete feedback and include your actual study minutes and any pacing difficulty in the existing feedback text. Submit once and wait for <b>Response received</b>. On slide 44, verify that receipt and save your corrected work; do not resubmit. This form does not establish individual attendance.')
 d.p('Primary method descriptions: <link href="'+NIST+'Herington.htm"><u>NIST area/Herington</u></link>; <link href="'+NIST+'Point.htm"><u>NIST point test</u></link>; <link href="'+NIST+'VanNess.htm"><u>NIST Van Ness</u></link>. Lab 03 uses explicitly documented teaching variants. Its local operator is a three-point derivative of g, not NIST TDE\'s fitted Padé point test. Reference numerical results were checked against the shipped Lab engines.','small')
 d.finish()

def guide(output):
 d=Doc(output/'week03-lab-guide.pdf','Week 3 guide: Calculations and independent labs',4,'Calculation and Lab guide')
 d.page('From Gibbs-Duhem to a local calculation','Guide page 1 | Use with worksheet B/C. Follow the worked C4 example, then attempt C5 independently.')
 d.head('1. Establish the path before using a residual')
 d.p('At fixed T,P, x d ln γ₁+(1-x)d ln γ₂=0. Differentiate g=x ln γ₁+(1-x)ln γ₂: the derivative is L plus that weighted derivative sum, so dg/dx=L. In the hand tables g means gᴱ/(RT), not total mixing Gibbs energy.')
 d.p('On a general path, Σxᵢd ln γᵢ=-hᴱdT/(RT²)+vᴱdP/(RT). Isothermal VLE can have varying pressure; the teaching analysis neglects the excess-volume pressure term. A real isobaric local assessment needs independent hᴱ. A missing correction is not a failed measurement.')
 d.head('2. The g-first calculation used in C4/C5')
 d.p('<b>Step 1:</b> calculate g at all three compositions, with each row\'s own x weight. <b>Step 2:</b> calculate L at the middle point. <b>Step 3:</b> on these equally spaced grids, slope≈(g<sub>right</sub>-g<sub>left</sub>)/(x<sub>right</sub>-x<sub>left</sub>). <b>Step 4:</b> subtract center L to obtain r.')
 d.table([['C4 value','Clean','Changed upper ln γ₁=0.36'],['g(0.40)','0.48','0.48'],['g(0.50)','0.50','0.50'],['g(0.60)','0.48','0.504'],['L(0.50)','0','0'],['Slope, then r','0; 0','0.120; +0.120']],widths=[140,145,CW-285])
 d.p('C4\'s changed g(0.60)=0.60×0.36+0.40×0.72. Keep all other values fixed. <b>Now close the worked table and do C5:</b> use its new numbers; do not copy C4\'s answer.','small')
 d.head('3. What the calculation does not establish')
 d.p('A single finite-difference r is not a dataset-average score. Noise, rounding and spacing affect derivatives. The simple centered formula above assumes uniform spacing; Lab 03 uses a three-point Lagrange derivative with the actual spacing. Three interior points cannot establish a full-range area test.')
 d.p('The clean hand tables come from smooth consistent model functions; the changed entries are deliberately perturbed synthetic values. A nonzero numerical residual indicates a discrepancy under the stated operator and assumptions. It does not uniquely identify an experimental cause.')
 d.head('4. Keep scope labels literal')
 d.p('<b>Not applicable:</b> wrong path for the method. <b>Not assessed:</b> missing required information. <b>Meets/outside this criterion:</b> a particular eligible numerical test. Avoid collapsing these into a single overall pass/fail label.')
 d.p('For C1/C2, retain signed trapezoids. The Lab\'s normalized D uses positive and negative area magnitudes and may be undefined near ideality; it is not signed S.','small')

 d.page('Lab 03: reproduce the demo, then test predictions','Guide page 2 | Worksheet D1-D5, 65-95 min. Watch the real baseline demo, then operate the Lab yourself.')
 d.link('Open Lab 03: Consistency tests','labs/consistency.html#consistency-experiment')
 d.head('D1. Baseline controls and two views')
 d.p('Set <b>Data set → Synthetic · isothermal, 350 K</b>, <b>Controlled perturbation → Consistent reference</b>, and <b>Sampling resolution → 41 points</b>. The default is 81, so change it explicitly. The synthetic hᴱ setting has no temperature contribution on this isothermal path.')
 d.p('Under <b>Inspect</b>, view <b>Log-activity ratio &amp; integrated area</b>, then <b>Local Gibbs-Duhem residual</b>. Record D, local score, both statuses and the chart pattern. Expand <b>Inspect data &amp; numerical results</b> if more digits are needed. Save the reference; wait until D5 for the fit.')
 d.head('D2-D3. Predict before the perturbation')
 d.p('Write both predictions on worksheet page 3 before selecting either defect. Then change <b>Controlled perturbation → Canceling errors · zero net area</b>; set <b>Amplitude=0.25</b>. Keep 41 points and the dataset unchanged. Results update automatically. Record D2 and save it.')
 d.p('Change only to <b>Localized defect near x₁ = 0.35</b>. Keep amplitude 0.25 and 41 points. Record D3 from both cards and charts. Locate the feature; do not infer the averaged status from the fact that a defect was inserted.')
 d.head('D4. Required sampling comparison')
 d.p('Keep the localized defect and amplitude fixed. Change <b>Sampling resolution → 161 points</b>. Record D4 and compare with D3. Note the score changes and peak location/appearance. The setting regenerates sampled synthetic data and changes numerical derivatives; it does not acquire new experimental measurements.')
 d.head('D5. One clean modeling run')
 d.p('Return to <b>Consistent reference / 41 points</b>. Click <b>Run modeling test →</b> once and wait for <b>Converged</b>. Under <b>Inspect → Modeling residuals</b>, record Δp (%) and Δy (percentage points). If convergence fails, report no modeling verdict. Save this result before changing inputs.')
 d.p('Use <b>Your conclusion</b> and <b>Export all results</b>. Rename files clean, canceling, localized-41 and localized-161. You may save a second clean file including the fit. The download is thermodynamic-consistency-study.json. Changing settings clears the previous fit.','small')
 d.p('<b>Optional reopen check:</b> expand <b>Study workspace · reopen and compare cases</b>. Under <b>Load studies or a comparison JSON</b>, select your exported file, then choose <b>Restore</b> beside its case. Check the restored controls and rerun <b>Run modeling test →</b> for a current fit. Imported results are recorded evidence, not a fresh calculation.','small')
 d.p('<b>Finish E1/E2:</b> an annotated residual plot, a comparison to your predictions, and a claim supported by numbers with a limitation. Take the 10-minute break at study minutes 95-105.','small')

 d.page('Lab 03: interpret what each method tests','Guide page 3 | Revisit during D5/E. This page explains methods, not the changed-case answers.')
 d.head('Area: a global integral')
 d.p('Let A be area above zero and B the positive magnitude below zero for L=ln(γ₁/γ₂). D=100|A-B|/(A+B). Lab 03 integrates line segments and uses D&lt;5% for its isothermal criterion, neglecting the excess-volume pressure term. Opposite local errors can cancel. Missing endpoints mean no full-range verdict unless an explicit extrapolation is assumed; near ideality D may be undefined.')
 d.head('Differential: a local relationship, then an average')
 d.p('r = d[gᴱ/(RT)]/dx - ln(γ₁/γ₂) + hᴱ/(RT²) dT/dx','eq')
 d.p('Lab 03 forms g first, takes three-point finite differences at interior points and reports <b>100 mean |r|</b>, with teaching threshold <b>5</b>. Isothermal data have no temperature term. Real isobaric data need independent hᴱ before a corrected verdict. Averages can conceal narrow features; inspect the curve. This is not the fitted Padé/Kojima test implemented in NIST TDE.')
 d.head('Herington: empirical isobaric allowance')
 d.p('J=150(T<sub>max</sub>-T<sub>min</sub>)/T<sub>min</sub>, using kelvin. The lab uses D-J&lt;10. J describes a boiling-range allowance, not measured hᴱ. Herington is not applicable to the required isothermal runs. Extrapolated endpoints give conditional results. The full NIST near-ideal decision tree is not implemented.')
 d.head('Van Ness-type: model reproduction')
 d.p('The isothermal fit uses two constant NRTL τ values with α=0.47 fixed. Δp=mean[100|Pcalc-Pobs|/Pobs]; Δy=mean[100|ycalc-yobs|]. Both Δp&lt;1% and Δy&lt;1 percentage point must hold. This teaching parameterization is not NIST TDE\'s five-parameter model. Small errors show reproduction, not independent predictive validation. Failure can involve model flexibility, property assumptions or data.')
 d.head('Build an inspectable conclusion')
 d.p('Label the chart axes and its case/resolution. Write a specific claim, give two relevant numerical or graphical observations, then state one limitation. Preserve unexpected results and explain a changed prediction. Do not treat resolution as new measurements or a numerical threshold as a universal physical law.')
 d.p('Exports save locally; they do not submit assignments. Use the actual file names/settings so the comparison can be reproduced. The generator is independent of the Lab 08 demonstration data.','small')
 d.p('Sources: <link href="'+NIST+'Herington.htm"><u>NIST Herington</u></link> | <link href="'+NIST+'Point.htm"><u>NIST point test</u></link> | <link href="'+NIST+'VanNess.htm"><u>NIST Van Ness</u></link>. See the Lab\'s Sources &amp; scope for implementation limits.','small')

 d.page('Lab 04: three feeds and an independent energy check','Guide page 4 | F/G, 105-155 min. Predict at slide 34, watch slide 35, then rerun at slide 36.')
 d.link('Open Lab 04: Liquid stability and LLE','labs/stability.html#lle-experiment')
 d.p('<b>Before watching:</b> complete G1 predictions during the 3-minute pause on slide 34. Watch the complete screen demonstration on slide 35. Then use the 25-minute pause on slide 36 to rerun G2-G4 yourself; keep your original predictions and your own calculation record.','small')
 d.head('1. Fix the model; compare three feeds')
 d.p('Set <b>Liquid model → Margules · 1 parameter</b> and <b>Interaction parameter A → 3</b>. For <b>Feed mole fraction z₁</b>, run 0.02, 0.12 and 0.50. After typing, click <b>Find equilibrium →</b>; sliders update immediately. Choose <b>View → Gibbs energy &amp; common tangent</b>.')
 d.p('After predicting, the corresponding <b>Explore a state</b> presets are a shortcut. Their names disclose the homogeneous-feed labels. Check the A and z values after selection. The hypothetical model has no T/P controls; hold A fixed for this comparison.','small')
 d.head('2. Record the feed and equilibrium separately')
 d.p('Record <b>Homogeneous feed</b>, the final phase label, <b>Gibbs energy decrease / RT</b>, and curvature sign. For two liquids record <b>Coexisting composition x₁ᵅ</b>, <b>x₁ᵝ</b> and <b>Fraction of β liquid</b>. β is the component-1-rich liquid, not vapor. For one liquid, report x₁=z₁; coexistence fractions do not apply.')
 d.p('Expand <b>Verify the equilibrium</b>. Inspect chemical-potential agreement, material balance and full tangent evidence. Positive curvature is local evidence, not proof of global stability. A named unstable or metastable feed can end in a stable two-liquid equilibrium.')
 d.head('3. Do the independent calculations')
 d.p('For z₁=0.12 and 0.50, use the actual endpoints in fβ=(z₁-xᵅ)/(xᵝ-xᵅ). Compute fα and reconstruct z₁. Both fractions must lie in [0,1]. Explain what goes wrong if those two endpoints are used for z₁=0.02.')
 d.p('For G4 use m(x)=x ln x+(1-x)ln(1-x)+3x(1-x). Evaluate m(0.12), then the weighted endpoint energy and their difference. Use natural logarithms. This includes ideal mixing; C used excess Gibbs energy only. Annotate the tangent and compare your result with the Lab energy decrease.')
 d.head('4. Save evidence and close the lesson')
 d.p('Type your reasoning in <b>Your explanation</b>, then click <b>Export study JSON</b> for each feed. Rename liquid-stability-study.json with z002, z012 or z050. Keep your prediction table, balances, energy calculation and annotated tangent. Small rounding residuals are expected if displayed endpoints are truncated.')
 d.p('<b>Reopen a saved case:</b> expand <b>Study workspace · reopen and compare cases</b>, load the study JSON, then choose <b>Restore</b> beside its case. Check the restored A and z₁, then click <b>Find equilibrium →</b> to calculate again. Imported results remain recorded evidence; restoring inputs does not replace a fresh calculation.','small')
 d.p('Stop the required investigation at G4. An A sweep is optional within the block, not homework. At 155-170 min attempt H1-H4 before solutions; at 170-180 min complete the existing anonymous Session 3 form, then save all files. No attendance identity is collected.','small')
 d.finish()

def background(output):
 d=Doc(output/'preclass-week-03.pdf','Week 3 optional background: Consistency before LLE',3,'Optional background')
 d.page('First ask whether the properties agree','Optional background page 1 | Use within the lesson when needed. No compulsory extra pre-reading.')
 d.p('Start the required route at <link href="'+BASE+'week03-study.html"><u>week03-study.html</u></link>. The video, six-page practice record and four-page guide supply the main route. This reading explains the concepts without adding another required session.')
 d.head('A fit and a thermodynamic constraint answer different questions')
 d.p('In Week 2, VLE measurements were used to infer γᵢ and fit models. The low-pressure expression γᵢ=yᵢP/(xᵢPᵢ<super>sat</super>) assumes ideal vapor, negligible Poynting correction and applicable vapor-pressure data. Fitting residuals show reproduction under those assumptions. Consistency asks whether the inferred properties obey thermodynamic relationships.')
 d.head('One excess Gibbs function constrains two coefficients')
 d.p('For a binary liquid, g=gᴱ/(RT)=x ln γ₁+(1-x)ln γ₂. Its composition derivative contains ln γ₁-ln γ₂ plus x d ln γ₁/dx+(1-x)d ln γ₂/dx. At fixed T,P the latter sum vanishes by Gibbs-Duhem, giving dg/dx=ln(γ₁/γ₂). A local comparison tests this derivative relationship.')
 d.p('Along a general path, Σxᵢd ln γᵢ=-hᴱdT/(RT²)+vᴱdP/(RT). Isothermal VLE may vary in pressure; the teaching diagnostic neglects its excess-volume pressure term. Isobaric VLE varies in temperature and requires independent excess enthalpy for the corrected local assessment. Missing information does not make a test passed or failed.')
 d.head('A numerical derivative requires a stated procedure')
 d.p('The worksheet forms g at each supplied composition, differences g and subtracts the center log ratio. On a uniform grid, the centered slope is (g<sub>right</sub>-g<sub>left</sub>)/(x<sub>right</sub>-x<sub>left</sub>). Lab 03 uses the corresponding three-point formula for actual spacing. Finite differences are approximations and may amplify noise. More sampled synthetic points do not create more independent experimental evidence.')
 d.p('C4/C5 are small fixed-T,P tables. Calculate them before using the Lab score. A single r is distinct from the dataset summary 100 mean |r|. Neither a one-point check nor three interior observations supplies a full-range area verdict.')
 d.head('Four questions to keep separate')
 d.table([['Question','Evidence'],['Did the numerical solver converge?','Stopping/residual checks'],['Are thermodynamic constraints compatible?','Applicable diagnostics and assumptions'],['Does a model reproduce observations?','Fitting errors for that selected model'],['Does it predict independent data?','Evaluation on observations excluded from fitting']],widths=[238,CW-238])

 d.page('Global areas and local residuals','Optional background page 2 | Revisit after your Lab 03 predictions if you want the mechanism of the controlled defects.')
 d.head('Integrating is a useful reduction, but it loses location')
 d.p('The area method integrates L=ln(γ₁/γ₂) over the full composition range. The hand example uses x=0,0.25,0.50,0.75,1 and L=2,1,0,-1,-2. Its trapezoids sum to zero; adding 0.20 everywhere adds 0.20 to the signed integral. Analytic endpoint limits are supplied, rather than inferred from interior observations.')
 d.p('Lab 03 reports D=100|A-B|/(A+B), with A/B the nonnegative areas above/below zero. This normalized difference is not the signed integral. It can be undefined near ideality. Extrapolating unknown endpoints supplies an assumption, not measurements.')
 d.head('A controlled defect separates the questions')
 d.p('Let f=0.25 cos(2πx). Adding (1-x)f to ln γ₁ and -xf to ln γ₂ cancels in the weighted g but changes L by f. The full-range integral of f is zero while f is nonzero locally. The continuous local residual therefore changes by -f. The construction is deliberately inconsistent and demonstrates a diagnostic limitation, not a real chemical mixture.')
 d.p('A narrow localized defect provides a different challenge. A residual plot can show a peak while its average is small. Meeting an aggregate criterion does not imply that every local feature is negligible. In D4, compare 41 and 161 sampled points with all other settings fixed and report the actual change rather than assuming improvement.')
 d.head('Other approaches have their own scope')
 d.p('<b>Herington:</b> an empirical isobaric boiling-range allowance J=150(Tmax-Tmin)/Tmin, with kelvin temperatures and a D-J criterion. J is not measured hᴱ. It does not apply to the required isothermal runs.')
 d.p('<b>Van Ness-type:</b> test whether a chosen consistent model reproduces pressure and vapor composition. Lab 03 uses a teaching NRTL parameterization. Failure can reflect model flexibility, property approximations or data; close reproduction is not independent predictive validation.')
 d.p('<b>Local diagnostic:</b> finite differences of g, with a temperature correction where required. Lab 03 is not the fitted Padé/Kojima point-test implementation in NIST TDE. Its score and thresholds are teaching choices and should be reported with that scope.')
 d.p('A useful conclusion includes the settings, literal result/status, plot evidence and limitation. An overall “passed” label hides which physical and numerical questions were actually evaluated.')
 d.p('Primary descriptions: <link href="'+NIST+'Herington.htm"><u>NIST Herington</u></link>; <link href="'+NIST+'Point.htm"><u>NIST point test</u></link>; <link href="'+NIST+'VanNess.htm"><u>NIST Van Ness</u></link>. The Lab states its departures in Sources &amp; scope.','small')

 d.page('Then ask which liquid state is stable','Optional background page 3 | Use after the consistency activities and the 95-105 minute break.')
 d.head('Consistency does not require one stable liquid')
 d.p('A Gibbs-Duhem-consistent model may have a nonconvex mixing-energy curve. At fixed T,P, equilibrium minimizes total Gibbs energy among admitted states satisfying material balances. Equal chemical potentials or solver convergence identifies a candidate; global stability still needs checking.')
 d.p('The common tangent between distinct compositions xᵅ/xᵝ has equal slopes and equal chemical potentials. It must support the whole admitted curve from below. Its segment gives the energy of realizable mixtures of the two endpoint liquids. Outside that segment, its extension is not a mixture with nonnegative amounts.')
 d.head('A homogeneous feed has a local and a global classification')
 d.p('<b>Stable:</b> no allowed split lowers its energy. <b>Metastable:</b> positive local curvature, yet a finite split lowers total energy. <b>Unstable:</b> negative curvature permits infinitesimal composition changes to lower energy. These labels describe the hypothetical homogeneous feed, not the final equilibrium phase count.')
 d.p('For symmetric Margules A=3, the investigation compares z₁=0.02, 0.12 and 0.50. Predict first, then inspect the computed energy curve. Use the actual calculated endpoints and phase fractions, not the illustrative hand values 0.20 and 0.80.')
 d.head('Balances and energies provide different evidence')
 d.p('fβ=(z₁-xᵅ)/(xᵝ-xᵅ), fα=1-fβ, z₁=fαxᵅ+fβxᵝ. Require 0≤fα,fβ≤1. A correct balance establishes feasibility, not the minimum energy. At z₁=0.02, extending the A=3 coexistence endpoints would require a negative amount and is inadmissible.')
 d.p('For this model, m(x)=Δg<sub>mix</sub>/(RT)=x ln x+(1-x)ln(1-x)+3x(1-x). This includes ideal mixing plus excess energy. Compare m(z₁) with fαm(xᵅ)+fβm(xᵝ). At a metastable feed, a finite energy decrease can coexist with positive local curvature.')
 d.head('Required evidence and optional extensions')
 d.p('Complete the three-feed record, two independent balances and the z₁=0.12 energy calculation. Annotate the supporting tangent and retain corrections to your predictions. Changing A explores different model behavior; it is an optional extension, not an additional required task. NRTL comparisons, LLE fitting and VLLE are also optional later work.')
 d.p('The model does not calculate nucleation barriers, interfacial energy, kinetics or domain patterns. A stable-equilibrium calculation does not predict how quickly separation occurs.','small')
 d.p('Original course explanation. Textbook reading locator from the supplied contents: sections 11.1-11.2, 14.11 and 16.2-16.4 for the stability bridge. No textbook text or figures are reproduced.','small')
 d.finish()

def validate_hand_examples():
 """Independently derive the numerical answers used in C, G and H."""
 import math
 def residual(xs,l1,l2):
  g=[x*a+(1-x)*b for x,a,b in zip(xs,l1,l2)]
  slope=(g[2]-g[0])/(xs[2]-xs[0])
  return g,slope,slope-(l1[1]-l2[1])
 checks={}
 checks['C4_clean']=residual([.4,.5,.6],[.72,.50,.32],[.32,.50,.72])
 checks['C4_changed']=residual([.4,.5,.6],[.72,.50,.36],[.32,.50,.72])
 checks['C5_clean']=residual([.3,.4,.5],[.735,.540,.375],[.135,.240,.375])
 checks['C5_changed']=residual([.3,.4,.5],[.735,.540,.375],[.135,.240,.425])
 for name,expected in [('C4_clean',0),('C4_changed',.12),('C5_clean',0),('C5_changed',.125)]:
  assert abs(checks[name][2]-expected)<1e-12,(name,checks[name])
 xa=.07072018167994476;xb=1-xa;z=.12
 m=lambda x:x*math.log(x)+(1-x)*math.log1p(-x)+3*x*(1-x)
 fb=(z-xa)/(xb-xa);fs=(1-fb)*m(xa)+fb*m(xb)
 assert abs((1-fb)*xa+fb*xb-z)<1e-12
 assert abs(m(z)-fs-.0082163581687304)<1e-12
 checks['G3_G4']={'xAlpha':xa,'xBeta':xb,'fractionBeta':fb,'feedEnergy':m(z),'splitEnergy':fs,'gain':m(z)-fs}
 checks['H1_residual']=(.48-.32)/(.4-.2)-.75
 checks['H3_fractionBeta']=(.39-.15)/(.75-.15)
 assert abs(checks['H1_residual']-.05)<1e-12
 assert abs(checks['H3_fractionBeta']-.4)<1e-12
 return checks

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--only-background',action='store_true');a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True)
 validate_hand_examples()
 if not a.only_background:
  practice(a.output);solutions(a.output);guide(a.output)
 background(a.output)

if __name__=='__main__':main()
