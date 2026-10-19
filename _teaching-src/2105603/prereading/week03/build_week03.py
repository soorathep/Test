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
 def table(self,rows,widths=None,minh=None):
  rows=[[Paragraph(str(v),ST['table']) for v in row] for row in rows]
  t=Table(rows,colWidths=widths or [CW/len(rows[0])]*len(rows[0]),rowHeights=minh)
  t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Body'),('BACKGROUND',(0,0),(-1,0),C['paper']),('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.6,C['mist']),('INNERGRID',(0,0),(-1,-1),.4,C['mist']),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
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
 d=Doc(output/'week03-practice.pdf','Week 3 practice: Consistency before LLE',4,'Practice record')
 d.page('Consistency before LLE','Page 1: minutes 0-50 | Write on this sheet or in a notebook using the same question labels.')
 d.p('Start at <link href="'+BASE+'week03-study.html"><u>week03-study.html</u></link>. Read the Week 3 slides in order. Use the lab guide only when directed. All required work fits within 180 minutes; the background reading is optional.','small')
 d.head('A. Retrieve the VLE ideas | 0-15 min')
 q(d,'A1.','Define x<sub>1</sub>, y<sub>1</sub>, z<sub>1</sub> and γ<sub>1</sub>. Which describes the liquid composition?')
 q(d,'A2.','Calculate γ<sub>1</sub> = y<sub>1</sub>P/(x<sub>1</sub>P<sub>1</sub><super>sat</super>) using y<sub>1</sub>=0.704857144627, P=158.707198211 kPa, x<sub>1</sub>=0.5 and P<sub>1</sub><super>sat</super>=150 kPa. Compare with exp(0.399813). State the vapor assumption.')
 q(d,'A3.','What does a small fitted residual show? What thermodynamic question remains?')
 d.head('B. Read the constraint and its scope | 15-35 min')
 q(d,'B1.','At fixed T and P, complete: x<sub>1</sub>d ln γ<sub>1</sub> + (1-x<sub>1</sub>)d ln γ<sub>2</sub> = ____ . Can the two coefficients vary independently?')
 q(d,'B2.','For isothermal VLE, P may vary with composition. Which pressure-related term does our teaching diagnostic neglect? For an isobaric path, which independent property is needed for the local temperature correction?')
 q(d,'B3.','If a method says “not assessed” or “not applicable,” may you record “passed”? Explain.',0)
 d.head('C. Integrate by hand | 35-50 min')
 d.table([['x<sub>1</sub>','0','0.25','0.50','0.75','1'],['L = ln(γ<sub>1</sub>/γ<sub>2</sub>)','2','1','0','-1','-2']],widths=[159,70,70,70,70,CW-439])
 d.p('C1. Use S = Σ ½(L<sub>j</sub>+L<sub>j+1</sub>)(x<sub>j+1</sub>-x<sub>j</sub>). Find the positive, negative and signed areas. C2. Add 0.20 to every L and recalculate S. C3. Explain why a small S does not certify all observations. These synthetic endpoint limits are supplied analytically.','small')
 d.lines(2)
 d.page('Compare evidence, then explain','Page 2: minutes 50-90 | Open Lab 03 and lab-guide pages 1-2. Do not upload the Lab 08 data here.')
 d.link('Open Lab 03: Consistency tests','labs/consistency.html#consistency-experiment')
 d.head('D. Controlled Lab 03 comparison | 50-80 min')
 d.p('<b>D1.</b> Select <b>Synthetic · isothermal, 350 K</b>, <b>Consistent reference</b> and <b>41 points</b>. Read the area and local-residual cards and both charts. Record D1. Save the reference evidence before changing the setting; wait until D4 to run the model fit.')
 d.p('<b>D2.</b> Change only <b>Controlled perturbation</b> to <b>Canceling errors · zero net area</b>; set <b>Amplitude = 0.25</b>. Record both scores and the local pattern. <b>D3.</b> Change only the perturbation to <b>Localized defect near x₁ = 0.35</b>. Inspect the peak as well as the averaged score.')
 d.table([['41-point isothermal case','Area D (%) / status','Local score / status','Pattern in residual chart'],['D1. Consistent reference','<br/><br/>','<br/><br/>','<br/><br/>'],['D2. Canceling, +0.25','<br/><br/>','<br/><br/>','<br/><br/>'],['D3. Localized, +0.25','<br/><br/>','<br/><br/>','<br/><br/>']],widths=[136,117,117,CW-370])
 q(d,'D4.','At minutes 74-80, return to Consistent reference and click Run modeling test → once. Record clean-reference Δp (%) and Δy (percentage points). Why is Herington not applicable here? What does the modeling test establish?',2)
 d.p('For each case, type a short note in <b>Your conclusion</b> and click <b>Export all results</b>. Rename the downloaded JSON as clean, canceling or localized. Changing settings clears the previous fit. Optional, only within this block: compare 41 with 161 points.','small')
 d.head('E. Correct an overclaim | 80-90 min')
 q(d,'E1.','Explain how the area criterion can be met while the local relationship fails. Why might an averaged local score also miss a narrow defect?',2)
 q(d,'E2.','Write one conclusion with (i) a claim, (ii) numerical/chart evidence, and (iii) an assumption or limitation.',2)
 d.p('<b>90-100 min: take a 10-minute break. Resume on practice page 3.</b>','small')
 d.page('From a consistent model to two liquids','Page 3: minutes 100-165 | Read the LLE slides, then open Lab 04 and lab-guide page 3.')
 d.head('F. Stability and a hand calculation | 100-120 min')
 q(d,'F1.','Does an equal-chemical-potential or stationary solution automatically give stable equilibrium? State the global criterion.')
 d.p('<b>F2.</b> For this hand example only, a supported tie line has x<sup>α</sup>=0.20 and x<sup>β</sup>=0.80. Find f<sub>β</sub>=(z<sub>1</sub>-x<sup>α</sup>)/(x<sup>β</sup>-x<sup>α</sup>) and f<sub>α</sub>=1-f<sub>β</sub> for z<sub>1</sub>=0.50 and 0.35; verify the component-1 balance.')
 d.lines(2)
 q(d,'F3.','A common tangent must support the entire admitted Gibbs-energy curve from below. Why is “touches at two points” insufficient?')
 d.head('G. Individual Lab 04 investigation | 120-165 min')
 d.link('Open Lab 04: Liquid stability and LLE','labs/stability.html#lle-experiment')
 d.p('<b>G1.</b> Predict first. Select <b>Liquid model: Margules · 1 parameter</b>, enter <b>A = 3</b> and <b>Feed mole fraction z₁ = 0.50</b>, then click <b>Find equilibrium →</b>. Use <b>View: Gibbs energy &amp; common tangent</b>. Record the actual computed endpoints and fractions below.')
 d.p('<b>G2.</b> Change <b>only z₁ to 0.35</b> and click <b>Find equilibrium →</b>. Keep A and the model fixed. This lab represents one fixed thermodynamic condition; there are no T or P controls. The hand-example endpoints above are <b>not</b> the expected Lab 04 outputs.','small')
 d.table([['z₁','x₁ᵅ','x₁ᵝ','fα','fβ','Feed state'],['0.50','<br/>','<br/>','<br/>','<br/>','<br/>'],['0.35','<br/>','<br/>','<br/>','<br/>','<br/>']],widths=[47,96,96,75,75,CW-389])
 q(d,'G3.','Independently evaluate f<sub>α</sub>x<sup>α</sup>+f<sub>β</sub>x<sup>β</sup> for z₁=0.35. Compare with “Verify the equilibrium.”',2)
 q(d,'G4.','Which quantities stay fixed as z changes? Which change? Use the tangent and energy decrease to justify two liquids.',2)
 d.p('Save each run using <b>Export study JSON</b>; rename with z050 or z035. Add your explanation before exporting. Stop after G4. LLE fitting and VLLE are optional later extensions, not required today.','small')
 d.page('Check understanding and close the lesson','Page 4: minutes 165-180 | Attempt H1-H4 before opening the separate worked solutions.')
 d.head('H. Self-review | 165-172 min')
 q(d,'H1.','The area criterion is met. Does that guarantee every point is thermodynamically consistent? Give one reason.',2)
 q(d,'H2.','A local diagnostic is outside its criterion. What should you check before attributing the discrepancy to experimental error?',2)
 q(d,'H3.','A model has small Δp and Δy on the fitting data. Does this establish predictive accuracy on new data? Explain.',2)
 q(d,'H4.','For supported xᵅ=0.20, xᵝ=0.80 and z₁=0.35, give fβ and the balance. State the additional condition that makes this a stable tie line.',2)
 d.link('After attempting H1-H4: open worked solutions','files/week03-solutions.pdf')
 d.head('I. Exit ticket, feedback and saved evidence | 172-180 min')
 d.p('<b>172-177 min:</b> open the existing <b>Session 3</b> form. In its <b>concept</b> response, answer the existing LLE question using your Lab 04 result. In its <b>evidence</b> response, include the Lab 03 area-versus-differential comparison: name the case, scores and one limitation. Use your own explanation.','small')
 d.p('<b>177-180 min:</b> complete the feedback section and submit. Save this practice record and your Lab 03 / Lab 04 JSON files or screenshots in your own folder. Lab exports save files locally; they do not submit to a server. The anonymous form does not establish individual attendance.','small')
 qr(d)
 d.p('Finished: completed A-I; attempted before solutions; compared charts and criteria; checked a material balance; submitted Session 3 exit ticket and feedback. No compulsory extra homework or pre-reading.','small')
 d.finish()

def solutions(output):
 d=Doc(output/'week03-solutions.pdf','Week 3 worked solutions: Consistency before LLE',3,'Worked solutions')
 d.page('A-C. Retrieve, qualify, integrate','Use after attempting the questions. All numerical data in these exercises are synthetic teaching data.')
 d.head('A. VLE and the meaning of a fit')
 d.p('<b>A1.</b> x₁ is liquid mole fraction; y₁ is vapor mole fraction; z₁ is overall mole fraction. γ₁ is the dimensionless liquid activity coefficient for the chosen pure-liquid standard state. Activity is a₁=γ₁x₁, not γ₁ alone.')
 d.p('<b>A2.</b> γ₁ = (0.704857144627 × 158.707198211)/(0.5 × 150) = <b>1.49154537</b>. exp(0.399813) ≈ <b>1.49154575</b>; the difference is rounding. This inference assumes ideal vapor and negligible Poynting correction, with applicable saturation pressure data.')
 d.p('<b>A3.</b> A small fitted residual shows reproduction by the selected model under its property assumptions. It does not establish thermodynamic consistency of all observations or accuracy on independent data.')
 d.head('B. A constraint with a thermodynamic path')
 d.p('<b>B1.</b> x₁ d ln γ₁ + (1-x₁)d ln γ₂ = <b>0 at fixed T and P</b>. Activity coefficients from one excess Gibbs-energy function cannot vary independently.')
 d.p('<b>B2.</b> More generally, Σxᵢ d ln γᵢ = -hᴱ/(RT²) dT + vᴱ/(RT) dP, with molar excess properties. Isothermal VLE can have variable P; our model neglects the excess-volume pressure term. For an isobaric local diagnostic, independently supplied hᴱ is needed for the temperature correction. Synthetic hᴱ in Lab 03 is generator information, not experimental calorimetry.')
 d.p('<b>B3.</b> No. “Not applicable” means the selected path is outside that method. “Not assessed” means required information is missing or disabled. Neither is a successful test.')
 d.head('C. Trapezoidal signed area is not normalized D')
 d.table([['Interval','Baseline trapezoid','After adding 0.20'],['0 to 0.25','0.25(2+1)/2 = 0.375','0.425'],['0.25 to 0.50','0.25(1+0)/2 = 0.125','0.175'],['0.50 to 0.75','0.25(0-1)/2 = -0.125','-0.075'],['0.75 to 1','0.25(-1-2)/2 = -0.375','-0.325'],['Signed sum S','0','0.200']],widths=[125,199,CW-324])
 d.p('<b>C1.</b> Positive area = 0.5; signed negative area = -0.5; S = 0. <b>C2.</b> Adding a constant 0.20 over a unit composition interval adds 0.20 to S. <b>C3.</b> The endpoint limits were provided analytically. Real interior observations do not determine missing endpoint intervals. Opposing local errors can cancel in the integral.')
 d.p('The lab reports D = 100|A-B|/(A+B), where A and B are nonnegative area magnitudes. D is undefined when its denominator is essentially zero. Do not label the signed S above as D.','small')
 d.page('D-E. Scores and charts must be read together','Reference engine values: isothermal 350 K; 41 points; perturbation amplitude +0.25. Small last-digit differences are numerical.')
 d.table([['Case','Area D (%)','Local score','Interpretation'],['Consistent reference','0.078692','0.117763','Both meet teaching criteria'],['Canceling errors','0.073552','15.598698','Area meets; local outside'],['Localized defect','2.013463','1.671839','Both meet; visible local peak']],widths=[132,90,90,CW-312])
 d.p('Isothermal area criterion: <b>D &lt; 5%</b>. Local teaching criterion: <b>100 mean |r| &lt; 5</b>. The local score is a scaled mean residual, not a probability, confidence level or percentage of bad observations. Finite integration/differentiation explains why the clean numerical values are small rather than exactly zero.','small')
 d.head('D1-D4. What each result permits')
 d.p('<b>D1.</b> The clean reference uses an independent Lab 03 generator, not the Lab 08 example parameter set. The clean modeling result is Δp ≈ <b>1.12 × 10⁻⁶%</b> and Δy ≈ <b>6.48 × 10⁻⁷ percentage points</b>. Near-zero reproduction is expected because the generating model is in the fit family.')
 d.p('<b>D2.</b> With f(x)=0.25 cos(2πx), the added log-ratio has zero full-range integral. It still violates the local relationship. Thus a small integrated error can conceal substantial structured local errors.')
 d.p('<b>D3.</b> The localized perturbation is narrow, centered near x₁=0.35. Its residual plot shows a peak, but averaging over the composition range dilutes it. At these exact settings <b>both aggregate criteria are met</b>. Do not report a failed averaged score merely because a defect was deliberately inserted.')
 d.p('<b>D4.</b> Herington is an empirical isobaric criterion, so it is not applicable to this isothermal dataset. The Van Ness-type run shows reproduction by the chosen NRTL model and property approximation. It does not prove consistency or prediction. Changing inputs clears the previous model fit; rerun if a new model result is required.')
 d.head('E1-E2. A defensible conclusion')
 d.p('The perturbation adds (1-x)f to ln γ₁ and -xf to ln γ₂. Their weighted sum gᴱ/(RT) is unchanged, while ln(γ₁/γ₂) increases by f. The exact local residual therefore changes by -f, apart from numerical differentiation error. Zero integral of f does not mean f is zero at every composition.')
 d.p('<b>Example conclusion:</b> “For the synthetic isothermal 41-point canceling-error case at amplitude 0.25, D=0.07355% meets the area criterion, while the local score 15.5987 exceeds 5 and the plot shows an oscillating residual. The integral misses canceling local discrepancies. This conclusion is conditional on the ideal-vapor, negligible-Poynting and negligible excess-volume pressure assumptions; the derivative score also depends on sampling.”')
 d.p('A real-data failure may arise from measurements, vapor-pressure correlations, omitted phase corrections, endpoint assumptions, model flexibility or numerical differentiation. It does not identify a unique cause.','small')
 d.page('F-I. A stable tie line, then phase amounts','Keep the supplied hand example separate from the actual Margules model calculation.')
 d.head('F1-F3. Hand calculation and stability')
 d.p('<b>F1 / F3.</b> Equal chemical potentials give an equilibrium candidate. Stable equilibrium minimizes total Gibbs energy over the admitted states at fixed T and P. A valid stable common tangent supports the whole admitted molar curve from below. Merely finding a stationary point or equal slopes is insufficient.')
 d.p('<b>F2.</b> For supplied xᵅ=0.20 and xᵝ=0.80: at z₁=0.50, fβ=(0.50-0.20)/0.60=<b>0.50</b>; at z₁=0.35, fβ=0.15/0.60=<b>0.25</b> and fα=<b>0.75</b>. The balance is 0.75(0.20)+0.25(0.80)=<b>0.35</b>.')
 d.head('G1-G4. Actual Lab 04: symmetric Margules A = 3')
 d.table([['z₁','x₁ᵅ','x₁ᵝ','fα','fβ'],['0.50','0.07072018','0.92927982','0.50000000','0.50000000'],['0.35','0.07072018','0.92927982','0.67471122','0.32528878']],widths=[47,120,120,111,CW-398])
 d.p('At z₁=0.35, fβ=(0.35-0.07072018)/(0.92927982-0.07072018)=<b>0.32528878</b>. Check 0.67471122(0.07072018)+0.32528878(0.92927982) ≈ <b>0.35000000</b>. Full-precision engine balance residual is near zero; rounded entries may leave a small residual.')
 d.p('Both hypothetical homogeneous feeds are <b>unstable</b>; equilibrium has <b>two liquids</b>. The Gibbs-energy decrease per RT is about <b>0.11519417</b> at z₁=0.50 and <b>0.09339471</b> at z₁=0.35. At fixed model and conditions, the coexisting compositions stay fixed while the phase fractions change.')
 d.p('A Gibbs-Duhem-consistent model may have a nonconvex mixing-Gibbs curve and predict phase separation. Consistency constrains derivatives; stability compares total Gibbs energies. A consistent model does not require a stable single liquid.')
 d.head('H1-H4. Brief self-check')
 d.p('<b>H1:</b> No; local errors can cancel. <b>H2:</b> Check the thermodynamic path, excess-property correction, phase/property assumptions and differentiation resolution/noise before blaming measurements. <b>H3:</b> No; fitting-data reproduction is not independent predictive validation. <b>H4:</b> fβ=0.25 and 0.75(0.20)+0.25(0.80)=0.35, provided the tangent supports the full admitted curve.')
 d.head('I. Finish with your own evidence')
 d.p('In Session 3, answer the existing LLE concept question from G; use the evidence field to explain D2 versus the clean reference. Complete feedback and save local files. There is no additional required task after the 180-minute lesson.','small')
 d.p('Method background: <link href="'+NIST+'Herington.htm"><u>NIST area / Herington</u></link>; <link href="'+NIST+'Point.htm"><u>NIST point test</u></link>; <link href="'+NIST+'VanNess.htm"><u>NIST Van Ness</u></link>. Lab 03 uses teaching variants, not the complete NIST TDE implementations. Exact reference values were computed from the shipped Lab 03 and Lab 04 engines.','small')
 d.finish()

def guide(output):
 d=Doc(output/'week03-lab-guide.pdf','Week 3 lab guide: Consistency before LLE',3,'Lab guide')
 d.page('Lab 03: use one controlled change','Guide page 1 | Use during practice D1-D4, minutes 50-80. No Excel upload or Lab 08 JSON is needed.')
 d.link('Open the Consistency Tests Lab','labs/consistency.html#consistency-experiment')
 d.head('1. Establish the reference and record it')
 d.p('Set <b>Data set → Synthetic · isothermal, 350 K</b>; <b>Controlled perturbation → Consistent reference</b>; <b>Sampling resolution → 41 points</b>. The page default is 81 points, so explicitly change it. Leave the synthetic Hᴱ checkbox as supplied; the thermal correction is zero on this isothermal path.')
 d.p('Read the scorecards. Under <b>Inspect</b>, choose <b>Log-activity ratio &amp; integrated area</b>, then <b>Local Gibbs-Duhem residual</b>. Copy D, the local score and the status into practice D1. These generated data are independent of the Lab 08 demo dataset.')
 d.p('Do not run the model yet. Compare the two controlled defects next; return to the clean reference for the single required model fit in D4. For numeric detail, expand <b>Inspect data &amp; numerical results</b>.')
 d.head('2. Insert canceling errors')
 d.p('Change <b>Controlled perturbation → Canceling errors · zero net area</b>. Set the <b>Amplitude</b> slider to <b>0.25</b>; check its displayed number. Keep the dataset and 41 points unchanged. The charts and scores update automatically. Record D2. Explain the difference between the integrated and local evidence.')
 d.head('3. Insert a narrow local defect')
 d.p('Change only <b>Controlled perturbation → Localized defect near x₁ = 0.35</b>. Keep amplitude 0.25 and 41 points. Record D3. Inspect the <b>Local Gibbs-Duhem residual</b> plot near 0.35. An averaged score can meet its threshold while a narrow peak remains visible.')
 d.p('Optional within the same 30-minute block: change <b>Sampling resolution</b> to <b>161 points</b>, note changes, then return to 41 before comparing with the reference answers. Resolution changes both sampling and numerical derivatives; it does not add experimental evidence.','small')
 d.head('4. Return to the reference for the modeling test')
 d.p('At minutes 74-80, return <b>Controlled perturbation → Consistent reference</b>. Keep 350 K and 41 points. Click <b>Run modeling test →</b> once. Wait for “Converged,” then record Δp and Δy in D4. If the fit fails, record no modeling verdict. Explain why Herington is not applicable to this path.')
 d.p('For each case, type the settings and interpretation in <b>Your conclusion</b>, then click <b>Export all results</b>. The download is <b>thermodynamic-consistency-study.json</b>. Rename each copy to include clean, canceling or localized. A screenshot of the local chart is also useful. Changing settings clears a previous fit, so record or export it first.')
 d.p('The JSON contains the settings, synthetic set, area and differential outputs, modeling result if run, and your explanation. Exporting saves locally; it is not a submission. Complete E1-E2 at minutes 80-90, then take the 10-minute break.','small')
 d.page('Lab 03: what the four methods mean','Guide page 2 | Read with the slides at minutes 15-35; revisit during D4 and E. The core practice is area plus local diagnostics.')
 d.head('Area: a global integral')
 d.p('L=ln(γ₁/γ₂); A is area above zero and B is the positive magnitude below zero. D=100|A-B|/(A+B). This lab uses piecewise-linear integration, and the isothermal criterion is <b>D &lt; 5%</b>, with the excess-volume pressure term neglected. Small signed area may conceal opposing local errors. Near ideality the normalization can be undefined. Missing endpoints mean no full-range verdict unless an explicit extrapolation is assumed.')
 d.head('Differential: a local relationship')
 d.p('With g=gᴱ/(RT)=x ln γ₁+(1-x)ln γ₂, the lab uses','body')
 d.p('r = dg/dx - ln(γ₁/γ₂) + hᴱ/(RT²) dT/dx','eq')
 d.p('The local score is <b>100 mean |r|</b>, with a teaching threshold of <b>5</b>. Three-point finite differences use interior points and actual composition spacing. This is <b>not</b> the fitted Padé/Kojima point test in NIST TDE. Derivatives amplify noise; inspect the plot, not just the averaged score. Isothermal data have no temperature term. For real isobaric data without independent hᴱ, the raw residual has no consistency verdict.')
 d.head('Herington: empirical allowance for an isobaric path')
 d.p('J=150(T<sub>max</sub>-T<sub>min</sub>)/T<sub>min</sub>, with temperatures in kelvin. This lab uses <b>D-J &lt; 10</b>. J is a boiling-range allowance, not measured hᴱ. It is <b>not applicable</b> to the required isothermal runs. Endpoint extrapolation yields a conditional result, not new measurements. The full NIST near-ideal decision tree is not implemented.')
 d.head('Van Ness-type: reproduction by a selected model')
 d.p('Clicking <b>Run modeling test →</b> fits NRTL jointly to P and y. Isothermal fits use two constant τ values with α=0.47 fixed. Δp=mean[100|Pcalc-Pobs|/Pobs]; Δy=mean[100|ycalc-yobs|]. Criteria are <b>Δp &lt; 1%</b> and <b>Δy &lt; 1 percentage point</b>. This is a teaching parameterization, not NIST TDE\'s five-parameter model. A bound hit is flagged. Small error shows reproduction; failure can reflect model flexibility, property approximations or data error.')
 d.head('Use the status literally')
 d.p('<b>Not applicable:</b> the method does not match the path. <b>Not assessed:</b> required information is missing or disabled. <b>Meets criterion:</b> this particular numerical criterion is met under its assumptions. None is a blanket certificate of data quality or prediction.','small')
 d.p('Sources: <link href="'+NIST+'Herington.htm"><u>NIST Herington</u></link> | <link href="'+NIST+'Point.htm"><u>NIST point test</u></link> | <link href="'+NIST+'VanNess.htm"><u>NIST Van Ness</u></link>. Inspect Lab 03 “Sources &amp; scope” for implementation and original data provenance.','small')
 d.page('Lab 04: separate equilibrium from amounts','Guide page 3 | Use during practice G1-G4, minutes 120-165. Complete F by hand first.')
 d.link('Open Liquid Stability & LLE','labs/stability.html#lle-experiment')
 d.head('1. Predict, then fix a reproducible state')
 d.p('At <b>For symmetric Margules with A &gt; 2, a feed near x₁ = 0.5…</b>, choose your prediction. Set <b>Liquid model → Margules · 1 parameter</b>, <b>Interaction parameter A → 3</b> and <b>Feed mole fraction z₁ → 0.50</b>. Click <b>Find equilibrium →</b>. Typing alone is not enough; this button applies typed values. Sliders update immediately.')
 d.p('Alternatively, <b>Explore a state → Unstable · A = 3, z₁ = 0.50</b> selects this example. Check all values before recording. These are hypothetical model parameters at fixed conditions, not a fitted chemical mixture. There are no T or P input boxes in this lab.','small')
 d.head('2. Read the actual common-tangent result')
 d.p('Choose <b>View → Gibbs energy &amp; common tangent</b>. Record <b>Coexisting composition x₁ᵅ</b>, <b>Coexisting composition x₁ᵝ</b>, and <b>Fraction of β liquid</b>. β is the component-1-rich liquid. Inspect <b>Homogeneous feed</b>, the phase label, and <b>Gibbs energy decrease / RT</b>. The feed classification describes the hypothetical single liquid; the equilibrium state may be two liquids.')
 d.p('Expand <b>Verify the equilibrium</b>. Check material balance, chemical potentials and tangent evidence. A common tangent must support the admitted curve from below. Positive local curvature alone cannot prove global stability; a metastable liquid can still lower its Gibbs energy by a finite split.')
 d.head('3. Change only the overall composition')
 d.p('Keep the model and A=3. Change <b>Feed mole fraction z₁ → 0.35</b>, then click <b>Find equilibrium →</b>. Record G2. Calculate fβ=(z₁-xᵅ)/(xᵝ-xᵅ), then independently check fαxᵅ+fβxᵝ=z₁ for G3. Use the lab endpoints, <b>not</b> the illustrative 0.20 and 0.80 from F2.')
 d.p('For G4, explain why endpoints stay fixed at the same model conditions while phase fractions change. State why the lower Gibbs energy supports two liquids. A consistent activity model can still predict a nonconvex Gibbs curve and liquid separation.')
 d.head('4. Save, self-check, submit the reflection')
 d.p('Type your explanation in <b>Your explanation</b>, then click <b>Export study JSON</b>. The download is <b>liquid-stability-study.json</b>. Rename copies with z050 and z035. Save the practice record. Do H1-H4 before opening the solutions, then use practice page 4 for the Session 3 exit ticket and feedback.')
 d.p('Stop after the required comparison. NRTL, two-parameter Margules, LLE fitting, VLLE and additional feed states are optional later investigations. They are not additional tasks for this 180-minute holiday lesson.','small')
 d.finish()

def background(output):
 d=Doc(output/'preclass-week-03.pdf','Week 3 optional background: Consistency before LLE',3,'Optional background')
 d.page('First ask whether the data agree with thermodynamics','Optional background page 1 | Not compulsory pre-reading. Use selected paragraphs within the 180-minute lesson if needed.')
 d.p('Start the required lesson at <link href="'+BASE+'week03-study.html"><u>week03-study.html</u></link>. The slides, practice record and exact lab guide provide the full route. No extra reading session is required.')
 d.head('From a fitted curve to a thermodynamic constraint')
 d.p('In Week 2, VLE observations were used to infer γᵢ and fit a model. The ideal-vapor relation γᵢ=yᵢP/(xᵢPᵢˢᵃᵗ) also assumes negligible Poynting correction and valid pure-component property data. Small fitting errors show reproduction under those assumptions. Thermodynamic consistency asks a separate question: are the inferred properties mutually compatible with thermodynamic identities?')
 d.p('At fixed T and P, the liquid coefficients obey the Gibbs-Duhem constraint:','body')
 d.p('x₁ d ln γ₁ + (1-x₁)d ln γ₂ = 0','eq')
 d.p('Both coefficients are derivatives of one excess Gibbs-energy function. They cannot be adjusted independently at every composition. For a general path, the right-hand side becomes -hᴱ dT/(RT²)+vᴱ dP/(RT), using molar excess enthalpy and volume. Isothermal VLE is not necessarily isobaric. The present teaching analysis neglects the excess-volume pressure contribution.')
 d.head('Global and local questions reveal different defects')
 d.p('The area approach integrates L=ln(γ₁/γ₂) over the full composition range. Contributions of opposite sign can cancel. A local derivative diagnostic instead compares the derivative of gᴱ/(RT) with L, with a temperature correction where needed. Numerical derivatives are sensitive to spacing and noise, and an average of local magnitudes may dilute a narrow defect. A plotted residual can therefore be informative even when a summary threshold is met.')
 d.head('Keep four questions separate')
 d.table([['Question','Evidence'],['Did the solver converge?','Numerical stopping and residual checks'],['Do thermodynamic constraints agree?','Applicable consistency diagnostics and assumptions'],['Does the model reproduce the data?','Fitting residuals for the selected model'],['Does it predict new observations?','Evaluation on data excluded from fitting']],widths=[227,CW-227])
 d.p('A consistency test is not a vote among badges. State the dataset, method, numerical evidence, applicable path and limitations. A missing correction or endpoint interval cannot be repaired by renaming “not assessed” as “passed.”','small')
 d.page('A worked area example and a local counterexample','Optional background page 2 | Synthetic endpoint limits are supplied, not inferred from sparse experimental data.')
 d.head('Integrate five known values')
 d.table([['x₁','0','0.25','0.50','0.75','1'],['L','2','1','0','-1','-2']],widths=[84,85,85,85,85,CW-424])
 d.p('The trapezoidal contributions are 0.375, 0.125, -0.125 and -0.375. Their sum is S=0. Positive area and negative-area magnitude are each 0.5. Adding 0.20 to every L gives S=0.20, because the composition interval has unit length. The signed S differs from normalized D=100|A-B|/(A+B).')
 d.head('An error can have zero total area')
 d.p('Let f(x)=0.25 cos(2πx). Add (1-x)f to ln γ₁ and -xf to ln γ₂. The weighted sum x ln γ₁+(1-x)ln γ₂ is unchanged, but L increases by f. Its full-range added area is zero. Nevertheless, the derivative of that weighted sum no longer matches L locally. This is the mechanism behind the canceling-error case in Lab 03.')
 d.p('A localized Gaussian defect is a second lesson. It can produce a visible peak while both the area criterion and averaged local score remain below their teaching thresholds. Inspect the shape and its location as well as the score. The controlled defects are intentionally nonphysical constructions for testing diagnostics, not measurements of a real mixture.')
 d.head('Other methods need their own interpretation')
 d.p('<b>Herington:</b> an empirical boiling-range allowance for isobaric data, using J=150(Tmax-Tmin)/Tmin in kelvin and the D-J criterion. This allowance is not independently measured hᴱ. It does not apply to the required isothermal exercise.')
 d.p('<b>Van Ness-type modeling:</b> compare observed pressure and vapor composition with a selected consistent activity model. The Lab 03 variant fits NRTL, with α=0.47 fixed. It asks whether that model reproduces the data. A failure may reflect the model or property approximation; a small residual does not establish prediction.')
 d.p('<b>Local differential diagnostic:</b> the lab uses three-point finite differences, not NIST TDE\'s fitted Padé point-test implementation. On a real isobaric path without independent hᴱ, the uncorrected residual has no thermodynamic verdict.')
 d.p('Reference descriptions: <link href="'+NIST+'Herington.htm"><u>NIST area / Herington</u></link>, <link href="'+NIST+'Point.htm"><u>NIST point test</u></link>, <link href="'+NIST+'VanNess.htm"><u>NIST Van Ness</u></link>. The lab states its departures from those implementations in “Methods” and “Sources &amp; scope.”','small')
 d.page('Then ask which liquid state is stable','Optional background page 3 | Consistency comes before stability, but neither question replaces the other.')
 d.head('A consistent model may predict two liquids')
 d.p('At fixed T and P, stable equilibrium minimizes total Gibbs energy over admitted states. Equal chemical potentials identify candidate coexisting compositions. Solver convergence, equal slopes or a local minimum alone does not establish the global minimum. A Gibbs-Duhem-consistent model can have a nonconvex mixing-Gibbs curve.')
 d.head('The common tangent compares one liquid with a split')
 d.p('For two coexisting compositions xᵅ and xᵝ on a molar Gibbs-energy curve g(x), the common slope equals [g(xᵝ)-g(xᵅ)]/(xᵝ-xᵅ). The connecting tangent must support the entire admitted curve from below. A line between the endpoints gives the Gibbs energy attainable by dividing material between those two liquids.')
 d.p('Negative curvature rules out local stability of a homogeneous liquid. Positive curvature does not guarantee global stability: a homogeneous state may be metastable because a finite split still lowers its Gibbs energy. The labels “unstable” and “metastable” describe the hypothetical homogeneous feed, not the final stable two-liquid state.')
 d.head('A material balance determines phase amounts')
 d.p('fβ=(z₁-xᵅ)/(xᵝ-xᵅ),  fα=1-fβ;  z₁=fαxᵅ+fβxᵝ','eq')
 d.p('For illustrative supported endpoints 0.20 and 0.80, z₁=0.50 gives equal fractions. Changing z₁ to 0.35 gives fβ=0.25 and fα=0.75. Check 0.75(0.20)+0.25(0.80)=0.35. The endpoints stay fixed at the same coexistence conditions; the amount ratio changes.')
 d.p('Lab 04 uses a different numerical model: symmetric Margules A=3. Its calculated endpoints are about 0.070720 and 0.929280, so z₁=0.35 gives fβ≈0.325289. Do not copy the illustrative hand endpoints into this model. Report which values were supplied and which were computed.')
 d.head('Use this bridge in the required lesson')
 d.p('Finish Lab 03 first. After the break, complete practice F by hand, then follow lab-guide page 3 for Lab 04. Use the actual computed endpoints and independently close the material balance. Finish with H1-H4, the Session 3 exit ticket and feedback. LLE fitting and VLLE remain optional extensions.')
 d.p('Original course explanation and examples. Textbook reading locator from the supplied contents: sections 11.1-11.2, 14.11 and 16.2-16.4 for the stability bridge. Method descriptions for consistency are linked on page 2. No textbook text or figures are reproduced.','small')
 d.finish()

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--only-background',action='store_true');a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True)
 if not a.only_background:
  practice(a.output);solutions(a.output);guide(a.output)
 background(a.output)

if __name__=='__main__':main()
