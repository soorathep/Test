"""Rebuild the three English Week 5 handouts using research Python.

Run with --output <directory>. This script contains the complete teaching text.
"""
from pathlib import Path
import argparse
import os
import tempfile
from xml.sax.saxutils import escape

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'week05-matplotlib'))
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
EXIT='https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=5'
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
  self.c.setFont('Bold',8.4);self.c.drawString(M,H-35,'2105603  /  WEEK 05  /  '+self.label.upper())
  self.c.setFillColor(C['graphite']);self.c.setFont('Body',7.5)
  self.c.drawString(M,27,'Advanced Chemical Engineering Thermodynamics | Independent lesson | 6 November 2026')
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
 doc.p('<b>Session 5 exit ticket + feedback</b>','small',width=CW-111,x=M+111)
 doc.p('Scan the QR or use the clickable link below. The form is anonymous. It is not an attendance-identification form.','small',width=CW-111,x=M+111)
 doc.p(f'<link href="{escape(EXIT)}" color="{skh.C["teal"]}"><u>Open the Session 5 form</u></link>','small',width=CW-111,x=M+111)
 doc.y=min(doc.y,top-size-7)

def practice(output):
 d=Doc(output/'week05-practice.pdf','Week 5 worksheet: Chemical equilibrium and routes to K',6,'Practice record')
 d.page('Start with the questions from Week 4','Page 1 | R1: slide 2, 4 min. R2: slide 3, 4 min. Check both at slide 4.')
 d.p('This independent lesson replaces the class on <b>6 November 2026</b>. We return to the classroom on <b>13 November</b>. Keep this one worksheet beside the video. Open Lab 12 and its two-page guide when directed. The solutions are for checking after each attempt.','small')
 d.p('<b>Planned route:</b> about 42 min of video, 128 min of calculations, Lab work and reflection, plus a 10 min break. No extra required preparation or follow-up assignment. At each pause limit, mark the unresolved step and continue. Bring your question on 13 November.','small')
 d.link('Week 5 lesson and resources','week05-study.html')
 d.head('R. Two kinds of equilibrium need a balance')
 d.p('Bulk sublimation has a separate pure solid phase. While that phase remains, the ideal-gas model gives P<sub>A</sub>=P<sub>sub</sub>(T). Surface adsorption uses an isotherm q(P<sub>A</sub>) per mass of adsorbent. In both cases, conserve the total inventory.','small')
 q(d,'R1.','At T=300 K, free gas volume V=1 L and Psub=10 kPa, the total volatile amount is nA=0.002 mol. Use R=8.314462618 kPa L mol⁻¹ K⁻¹. Calculate ncap=PsubV/(RT), decide whether solid remains, then calculate PA. Add 0.002 mol of ideal, nonadsorbing inert gas at the same T and V. Calculate Ptotal and state whether PA changes.',3)
 q(d,'R2.','A candidate Langmuir state has PA=10 kPa, T=300 K, Vg=1 L, ms=0.010 kg, qs=2 mol/kg and b=0.1 kPa⁻¹. The total feed is 0.010 mol. Independently calculate ngas=PAVg/(RT) and nads=ms qs bPA/(1+bPA). Does their sum equal the feed? Explain why a residual amount obtained by subtraction still needs an isotherm check.',3)
 d.head('What to keep')
 d.p('Keep first attempts and mark corrections separately. Save three completed Lab 12 studies: 12A (350 K, 100 kPa), 12B (350 K, 400 kPa), and 12C (400 K, 100 kPa). At the end, submit the Session 5 exit ticket and feedback once. Exported JSON files remain on your device.','small')
 d.p('If the Lab does not run, record the message or control that blocked you and keep the hand calculation. Continue at the time limit. An unresolved question is useful evidence for the next class.','small')

 d.page('Build the quotient and the driving force','Page 2 | A1-A3: slide 8, 10 min. B1: slide 10, 6 min. Check A at slide 9 and B at slide 14.')
 d.head('A. Synthetic A₂(g) ⇌ 2A(g)')
 d.p('Initially nA₂,0=1 mol, nA,0=0 and no inert gas. Define extent ξ in mol and the dimensionless fraction f=ξ/(1 mol). This synthetic model assumes one neutral ideal-gas reaction. The standard gas pressure is p°=100 kPa.')
 q(d,'A1.','Complete the mole table in terms of f. Give the feasible interval and show the conserved atom amount 2nA₂+nA.',1)
 d.table([['Quantity','A₂','A'],['Initial amount / mol','1','0'],['Reaction coefficient ν','−1','+2'],['Amount at extent ξ / mol','<br/>','<br/>'],['Mole fraction y','<br/>','<br/>']],widths=[180,164,CW-344],padding=5)
 q(d,'A2.','Use ai=yiP/p° and Q=aA²/aA₂. Derive Q in terms of f and P/p°. Explain why Q and P/p° are dimensionless.',2)
 q(d,'A3.','At f=0.50, calculate the amounts, mole fractions and Q at P/p°=1 and 4. Are these necessarily equilibrium states? Verify the atom balance.',2)
 d.head('B1. Direction before equilibrium')
 d.p('At T=350 K, ΔrG°=−4000 J/mol of reaction. Use ΔrG=ΔrG°+RT lnQ, with R=8.314462618 J mol⁻¹ K⁻¹.','small')
 q(d,'B1.','Calculate ΔrG at Q=1 and Q=10. For each, state whether increasing or decreasing extent lowers G at fixed T and P.',2)

 d.page('Calculate K, then calculate composition','Page 3 | B2-B4: slide 13, 10 min. C1-C3: slide 15, 15 min. Checks at slides 14 and 16.')
 d.head('B. Two consistent reference routes at 350 K')
 d.p('All properties are per mole of A₂ ⇌ 2A as written, on the same ideal-gas standard states. Direct ΔrG°=−4.000 kJ/mol. Reference ΔrH°=50.000 kJ/mol and ΔrS°=54000/350=154.285714 J mol⁻¹ K⁻¹. Use R=8.314462618 J mol⁻¹ K⁻¹.','small')
 q(d,'B2.','Calculate lnK=−ΔrG°/(RT), then K from the direct Gibbs energy. Show the kJ-to-J conversion.',2)
 q(d,'B3.','Calculate ΔrG°=ΔrH°−TΔrS°, then lnK and K. Keep units and the sign explicit.',2)
 q(d,'B4.','Explain the expected agreement. Does agreement between consistent synthetic definitions independently validate a real chemical system?',2)
 d.head('C. Reference equilibrium at 100 kPa')
 d.p('Use K=3.9532626 if your B calculation is unfinished. Set T=350 K and P=p°=100 kPa. Q=[4f²/(1−f²)](P/p°). Initial amounts remain 1 mol A₂ and no A.','small')
 q(d,'C1.','Set Q=K and rearrange for f². Choose the physically feasible positive root, then convert f to ξ in mol.',2)
 q(d,'C2.','Calculate nA₂, nA, yA₂ and yA. Keep enough digits for the checks.',2)
 q(d,'C3.','Recompute Q from activities. Verify 2nA₂+nA=2 mol of atoms. Explain why conserving total molecular moles would be incorrect for this reaction.',2)

 d.page('Pressure comparison and Lab 12','Page 4 | C4: slide 17, 8 min. D1: slide 19, 5 min. D2-D4: slide 21, 22 min. Guide p. 1.')
 d.head('C4. A controlled pressure change')
 q(d,'C4.','Keep T=350 K, p°=100 kPa and the initial inventory. Raise P from 100 to 400 kPa. Predict whether K and ξ change, then calculate ξ and both mole fractions. Explain using Q and Δν=+1.',3)
 d.head('D. Run the two pressure cases')
 d.link('Open Lab 12: Chemical equilibrium','labs/reaction.html#rx-experiment')
 q(d,'D1.','Before slide 20, reset the synthetic example and use guide p. 1 to check the reference data. Set ΔrCp°=0 (the default is 30) and select the direct Gibbs K source. Identify the evaluation T, reference T, actual P and standard p°.',1)
 d.p('<b>D2.</b> Run 12A at 350 K and 100 kPa. Compare direct Gibbs with the ΔH°/ΔS° constant-values route, then return to direct Gibbs. <b>D3.</b> Change only P to 400 kPa for 12B. Click <b>Compare K methods</b> after each change. Record the values below. Complete 12C later in F.','small')
 d.table([['Case','T / K','P / kPa','K','ξ / mol','yA₂ / yA'],['12A','350','100','<br/>','<br/>','<br/>'],['12B','350','400','<br/>','<br/>','<br/>'],['12C (F)','400','100','<br/>','<br/>','<br/>']],widths=[68,55,65,91,91,CW-370],padding=5)
 q(d,'D4.','For 12B, independently calculate Q from the equilibrium mole fractions and verify the atom balance. Label both axes of the Gibbs-energy graph and identify the minimum. Export each study and name it 12A or 12B on your device. Keep one assumption with your comparison.',3)
 d.p('<b>Read the correct panel.</b> The separate Observed activities panel uses independent input values yA₂=0.2 and yA=0.8. It is not automatically updated to the solver composition. Use <b>From K to equilibrium composition</b> for this table and your Q=K check.','small')
 d.p('At slide 23, take the 10-minute break. If a technical problem prevents a run, record it and retain your hand calculation. Do not invent a Lab result.','small')

 d.page('Temperature comparison and saved evidence','Page 5 | E1-E3: slide 26, 15 min. F1-F3: slide 29, 19 min. Guide p. 2. Checks at slides 27 and 30.')
 d.head('E. Constant-enthalpy van\'t Hoff route')
 d.p('Use Tref=350 K, lnKref=1.37454120049, ΔrH°=50000 J/mol and ΔrCp°=0 over 350-400 K. Keep P=p°=100 kPa and the original feed. The approximation assumes consistent reference data, no phase transition and valid constant reaction enthalpy.','small')
 d.p('ln[K(T)/Kref]=(ΔrH°/R)(1/Tref−1/T).','eq')
 q(d,'E1.','Before calculating, predict the direction of K when temperature rises to 400 K. Calculate the increment in lnK, then lnK(400) and K(400).',2)
 q(d,'E2.','Independently use ΔrG°(400)=50000−400(54000/350) J/mol and lnK=−ΔrG°/(R·400). Explain why this is consistent only under the same thermal assumptions.',2)
 q(d,'E3.','At 400 K and P/p°=1, calculate f, ξ, yA₂ and yA. Compare with 12A and check the atom balance.',2)
 d.head('F. Third Lab case and JSON restore')
 q(d,'F1.','Follow guide p. 2. For 12C, select van ’t Hoff · constant ΔH°, set T=400 K and P=100 kPa, then recalculate. Keep Tref and supplied Gibbs-data temperatures at 350 K. Complete row 12C on p. 4. Why is the direct Gibbs route unavailable at 400 K?',2)
 q(d,'F2.','Export the 12C complete study. Reopen 12A using Restore calculator study JSON. Verify T, P, K source, Cp and initial amounts, then confirm the fresh result matches your 12A record. Record one recovered number and its units.',2)
 q(d,'F3.','Write two sentences: why did 12A→12B change composition without changing K, and why did 12A→12C change both? Name one assumption that limits all three predictions.',2)

 d.page('Close the lesson and retain your evidence','Page 6 | G: slide 32, 10 min. Your required work ends after submission and saving your files.')
 d.head('G. Explain one result and report one difficulty')
 q(d,'G1.','Prepare your Session 5 explanation: distinguish K from Q and explain how pressure can change composition at fixed K. Give one numerical result or an independent Q/atom-balance check from your work. Include T, P, p°, reaction basis and relevant units.',4)
 q(d,'G2.','Record actual study time: ______ minutes. Pace: ______. If a step remains unclear, identify the worksheet item or Lab control and write what you tried. We will discuss questions in the classroom on 13 November.',3)
 d.head('Submit once')
 qr(d)
 d.p('Use the existing concept, evidence and feedback fields. English or Thai is welcome. Wait for <b>Response received</b>. The form is anonymous and does not identify individual attendance. If you already submitted this session, do not send a second entry merely to check the receipt.','small')
 d.head('Keep for the next class')
 d.p('One completed worksheet with corrections, the 12A/12B/12C complete-study JSON files, one controlled comparison, and one independent numerical check. Your calculator exports are local records, not automatic submissions.','small')
 d.p('<b>Optional references:</b> custom species, formation-energy detail and nonzero heat-capacity models are outside the required route. No additional preclass reading or after-class assignment is required.','small')
 d.link('Worked solutions: use after your attempts','files/week05-solutions.pdf')
 d.finish()

def guide(output):
 d=Doc(output/'week05-lab-guide.pdf','Week 5 Lab 12 guide',2,'Lab guide')
 d.page('Lab 12: two routes and one pressure change','Guide page 1 | Worksheet D, p. 4 | Setup at slide 19, demonstration at 20, independent work at 21.')
 d.link('Open the Chemical equilibrium Lab','labs/reaction.html#rx-experiment')
 d.p('Select <b>Reset synthetic example</b>. This restores defaults, including Cp=30 and a corrected van\'t Hoff route. Change the two settings below explicitly. Keep the reaction A₂ ⇌ 2A and formal atom counts supplied by the example.','small')
 d.table([['Field / control','Required setting'],['Evaluation temperature / K','350'],['Reference temperature / K','350'],['Gas standard pressure p° / kPa','100'],['Observation and extent pressure / kPa','100 for 12A; 400 for 12B'],['Nonreacting ideal gas in extent feed / mol','0'],['Direct ΔrG° / kJ per mol of reaction','−4; its data temperature remains 350 K'],['ΔrH°(Tref) / kJ mol⁻¹','50'],['ΔrS°(Tref) / J mol⁻¹ K⁻¹','154.28571428571428'],['Constant ΔrCp° / J mol⁻¹ K⁻¹','Change 30 to 0'],['Reference K input convention / value','ln Kref / 1.3745412004882978'],['K source for extent and driving force','Direct ΔrG° at its supplied T'],['Initial amounts in the species table','A₂: 1 mol; A: 0 mol']],widths=[280,CW-280],padding=4)
 d.head('12A: reference state and route check')
 d.p('1. Click <b>Compare K methods</b>. Inspect the method table, then <b>From K to equilibrium composition</b>. Record K, ξ, equilibrium mole fractions and the atom-balance residual.')
 d.p('2. Select <b>ΔH°/ΔS° · constant values</b> as K source. Recalculate and compare at 350 K. Return to <b>Direct ΔrG°</b>, recalculate, and click <b>Export complete study</b>. Name the downloaded file 12A or identify it clearly in your records.')
 d.head('12B: change only actual total pressure')
 d.p('3. Set actual pressure to <b>400 kPa</b>, leaving p°=100 kPa and T=350 K. Recalculate, record and export 12B. Compare with your hand calculation. Input changes invalidate old results.')
 d.p('<b>Two different Q contexts:</b> Observed activities uses independent input mole fractions 0.2 and 0.8. At 100 kPa these give Q=3.2, which differs from K. Use the <b>equilibrium composition</b> table for your solver Q=K check. Do not change the equilibrium assertion just to force agreement.','small')

 d.page('Lab 12: a temperature law and a restored study','Guide page 2 | Worksheet F, p. 5 | Attempt at slide 29. Demonstration and check at slide 30.')
 d.head('12C: raise temperature at the baseline pressure')
 d.p('1. Starting from your reference data, select <b>van ’t Hoff · constant ΔH°</b> for <b>K source for extent and driving force</b>. Set <b>Evaluation temperature=400 K</b> and actual <b>pressure=100 kPa</b>. Keep Cp=0, inert gas=0 and p°=100 kPa.')
 d.p('2. Keep Tref=350 K, lnKref=1.3745412004882978, Href=50 kJ/mol and Sref=154.28571428571428 J mol⁻¹ K⁻¹. The direct and formation Gibbs-data temperature labels stay at 350 K. Their point-data routes will be unavailable at 400 K. This is an applicability check, not a missing zero.')
 d.p('3. Click <b>Compare K methods</b>. Read the selected van\'t Hoff K and the equilibrium composition. Record 12C in the worksheet. Independently check Q and the atom inventory. Export the complete study as 12C.')
 d.head('Reopen an actual exported calculator study')
 d.p('4. In <b>Restore calculator study JSON</b>, choose your 12A complete-study file. This calculator control restores inputs and automatically recalculates. Verify 350 K, 100 kPa, direct Gibbs source, Cp=0, the initial amounts and the fresh result. Record one matching value.')
 d.p('5. Keep the three files and your worksheet. A restored record does not prove the physical model. It demonstrates that the saved settings can reproduce the calculation.')
 d.head('If you use Study workspace instead')
 d.p('Study workspace also imports studies or comparison JSON files. Its <b>Restore</b> action loads inputs; click <b>Compare K methods</b> afterward to obtain a fresh result. The two restore controls behave differently. A comparison file is optional for this lesson.','small')
 d.head('Troubleshooting and scope')
 d.p('If Export is disabled, recalculate after changing inputs. If extent is unavailable at 400 K, check that the selected K source is the constant-enthalpy van\'t Hoff route. Do not relabel the direct 350 K property as a 400 K property.','small')
 d.p('The extent solver assumes one neutral ideal-gas reaction at fixed T and total P. It excludes charged gas species, multiple reactions, nonideal EOS effects and phase splitting. Gas activity coefficients in the independent observations panel are not an EOS for this solver.','small')
 d.p('The temperature graph uses T on its horizontal axis and the selected logarithm of K on the vertical axis. With Cp=0 and mutually consistent reference data, some curves overlap. The reaction graph uses ξ / mol and [G(ξ)−G(0)]/(RT) / mol. Neither is a kinetic time trace.','small')
 d.p('<b>Stop rule:</b> use the worksheet pause budgets. If blocked, write the exact step or error, retain your hand calculations and continue. Bring the question on 13 November.','small')
 d.finish()

def solutions(output):
 d=Doc(output/'week05-solutions.pdf','Week 5 worked solutions',5,'Worked solutions')
 d.page('R: check phases, pressure and adsorption','Solution page 1 | Read only after attempting R1-R2. All values are synthetic teaching definitions.')
 d.head('R1. Fixed temperature and free volume')
 d.p('1. ncap=(10 kPa)(1 L)/[(8.314462618 kPa L mol⁻¹ K⁻¹)(300 K)]=<b>0.004009079 mol</b>.')
 d.p('2. Only 0.002 mol is available. Since this is less than ncap, all the volatile solid disappears: ngas=0.002 mol and nsolid=0.')
 d.p('3. PA=(0.002)(8.314462618)(300)/1=<b>4.988678 kPa</b>. The partial pressure is below Psub because the inventory is insufficient to saturate the gas.')
 d.p('4. Adding 0.002 mol inert at the same T and V gives Pinert=4.988678 kPa and <b>Ptotal=9.977355 kPa</b>. PA stays 4.988678 kPa under these ideal-gas, nonreacting, nonadsorbing assumptions.')
 d.p('The presence or absence of solid does not establish ideal-gas behavior. Ideal-gas behavior is an assumption of the model. At nA=ncap exactly, ngas=ncap, nsolid=0 and PA=Psub at the phase boundary.','small')
 d.head('R2. Check the candidate pressure independently')
 d.p('1. At PA=10 kPa, ngas=10×1/(8.314462618×300)=<b>0.004009079 mol</b>.')
 d.p('2. q=qs bPA/(1+bPA)=2×0.1×10/(1+0.1×10)=<b>1 mol/kg</b>. Thus nads=0.010 kg×1 mol/kg=<b>0.010000 mol</b>.')
 d.p('3. ngas+nads=<b>0.014009079 mol</b>, exceeding the specified 0.010 mol feed. Therefore 10 kPa is not the equilibrium pressure for this feed.')
 d.p('4. A numerical root of 0.010=PA/(R·300)+0.010[2×0.1PA/(1+0.1PA)] is <b>PA=6.080248 kPa</b>. It gives ngas=0.002437619 mol and nads=0.007562381 mol.')
 d.p('The final sum equals 0.010 mol, and both amounts satisfy their own equations at the same pressure. Simply defining nads=feed−ngas would close the sum without checking the isotherm.','small')

 d.page('A-B: quotient, driving force and two K routes','Solution page 2 | Checks for worksheet pp. 2-3. Use a consistent reaction and standard-state basis.')
 d.head('A1-A3. Mole table and dimensionless quotient')
 d.p('With f=ξ/(1 mol): nA₂=(1−f) mol, nA=2f mol and ntotal=(1+f) mol. Nonnegative amounts require 0≤f≤1. The atom inventory is 2(1−f)+2f=2 mol of atoms.')
 d.p('yA₂=(1−f)/(1+f), yA=2f/(1+f). For ideal gases ai=yiP/p°, so <b>Q=[4f²/(1−f²)](P/p°)</b>. This expression is finite and positive for 0&lt;f&lt;1.')
 d.p('At f=0.50: nA₂=0.50 mol, nA=1.00 mol, yA₂=1/3 and yA=2/3. Q=4/3 at P/p°=1 and Q=16/3 at P/p°=4. These trial states have not yet been required to satisfy Q=K.')
 d.head('B1. Driving force at 350 K')
 d.p('At Q=1, ΔrG=−4000+RT ln1=<b>−4000 J/mol</b>: increasing extent is favored.')
 d.p('At Q=10, ΔrG=−4000+(8.314462618)(350)ln10=<b>+2700.665 J/mol</b>: decreasing extent is favored.')
 d.head('B2. Direct Gibbs route')
 d.p('Convert −4.000 kJ/mol to −4000 J/mol. lnK=−(−4000)/(8.314462618×350)=<b>1.3745412</b>. K=exp(1.3745412)=<b>3.9532626</b>. K is dimensionless.')
 d.head('B3-B4. Enthalpy-entropy route and interpretation')
 d.p('ΔrG°=50000−350(54000/350)=50000−54000=<b>−4000 J/mol</b>. Substituting into the same Gibbs relation gives the same lnK and K.')
 d.p('The synthetic inputs were defined to agree at the reference temperature. Agreement checks consistent signs, units and reaction basis. It does not independently validate real-compound properties or the ideal-gas approximation.','small')
 d.p('K depends on temperature for a fixed reaction and standard-state convention. It is not the current reaction quotient unless the specified composition is at equilibrium.','small')

 d.page('C: solve the equilibrium and change pressure','Solution page 3 | Checks for worksheet pp. 3-4. Initial amounts: 1 mol A₂ and no A or inert gas.')
 d.head('C1. Rearrange Q=K')
 d.p('Write p=P/p°. K(1−f²)=4pf², so K=f²(K+4p). Therefore <b>f=√[K/(K+4p)]</b>. The positive root lies between 0 and 1 for K&gt;0 and p&gt;0.')
 d.head('C2-C3. Reference case at 350 K and 100 kPa')
 d.p('Here p=1 and K=3.9532626. f=√[3.9532626/(3.9532626+4)]=<b>0.7050261</b>. Hence ξ=0.7050261 mol.')
 d.table([['Quantity','Value'],['nA₂ / mol','0.294973941'],['nA / mol','1.410052118'],['ntotal / mol','1.705026059'],['yA₂','0.173002600'],['yA','0.826997400'],['Q = (yA²/yA₂)(P/p°)','3.953262552']],widths=[260,CW-260],padding=4)
 d.p('The atom check gives 2×0.294973941+1.410052118=2.000000000 mol of atoms. Total molecular moles increase because one A₂ molecule produces two A molecules. Conserving total molecular moles would contradict the stoichiometry.','small')
 d.head('C4. Same temperature, four times the pressure')
 d.p('At P=400 kPa, p=4 while K remains 3.9532626. f=√[K/(K+16)]=<b>0.4451136</b>, so ξ=0.4451136 mol.')
 d.p('nA₂=0.554886393 mol, nA=0.890227214 mol, yA₂=0.383974236 and yA=0.616025764. Recomputed Q remains 3.9532626 and the atom amount remains 2 mol.')
 d.p('At a fixed trial composition, Q is proportional to pressure for Δν=+1. Compression raises Q above the unchanged K, so the reverse reaction reduces extent until Q=K. This is a fixed-total-pressure equilibrium comparison, distinct from adding inert gas at fixed volume.','small')

 d.page('D: read the calculator and keep the right evidence','Solution page 4 | Worksheet p. 4. The guide provides exact controls, export and restore instructions.')
 d.head('D1-D3. Reference controls and the pressure comparison')
 d.p('Reset the synthetic example, then explicitly set Cp from 30 to <b>0</b> and the extent K source to <b>Direct ΔrG° at its supplied T</b>. Keep the standard pressure at 100 kPa. At 350 K, the direct Gibbs and constant H/S routes agree. Return to direct Gibbs before saving 12A and 12B.')
 d.table([['Case','T / K','P / kPa','K','ξ / mol'],['12A','350','100','3.953263','0.705026'],['12B','350','400','3.953263','0.445114']],widths=[75,70,80,135,CW-360])
 d.head('D4. Q and a conserved amount')
 d.p('For 12B, Q=(0.616025764²/0.383974236)×4=3.9532626. The atom check gives 2×0.554886393+0.890227214=2.0000000 mol of A atoms.')
 d.p('The reaction graph has ξ / mol on the horizontal axis and [G(ξ)−G(0)]/(RT) / mol on the vertical axis. The marked state is the minimum of this one-reaction ideal-gas model at fixed T and P. The relative energy reference can shift vertically without changing the minimum location.','small')
 d.head('A separate panel contains separate observations')
 d.p('The default observation table has yA₂=0.2 and yA=0.8. At 100 kPa it gives Q=0.8²/0.2=<b>3.2</b>, which differs from K=3.953263. At 400 kPa the same fractions give Q=12.8. This is expected for independent trial inputs.')
 d.p('The extent solver returns a different composition that satisfies Q=K. Do not interpret a nonzero driving force in the supplied-observation panel as failure of the equilibrium solver. Read the selected K-source label and the equilibrium-composition table.','small')
 d.head('What the checks establish')
 d.p('Agreement, a small lnQ−lnK residual and atom conservation support the calculation within the specified model. They do not validate real property data, the ideal-gas assumption, or the absence of additional reactions and phases.','small')
 d.p('If a run was blocked, retain the error and the independent calculation. A missing calculator value is not zero and is not evidence of a successful Lab run.','small')

 d.page('E-F: temperature law, restored evidence and completion','Solution page 5 | Worksheet pp. 5-6. Constant ΔH°=50 kJ/mol and ΔCp°=0 over 350-400 K.')
 d.head('E1. Integrated van\'t Hoff calculation')
 d.p('ln[K400/K350]=(50000/8.314462618)(1/350−1/400)=<b>2.1477206</b>. Add lnK350=1.3745412 to obtain <b>lnK400=3.5222618</b>, then <b>K400=33.8609295</b>.')
 d.head('E2. Consistent thermal cross-check')
 d.p('With the same constant H and S definitions: ΔrG°(400)=50000−400(54000/350)=<b>−11714.2857 J/mol</b>. Thus −ΔrG°/(R·400)=3.5222618. This agreement relies on ΔCp°=0 and the consistent reference values.')
 d.head('E3. Composition at 400 K and 100 kPa')
 d.p('f=√[33.8609295/(33.8609295+4)]=<b>0.9457009</b>. ξ=0.9457009 mol, nA₂=0.054299101 mol, nA=1.891401798 mol, yA₂=0.027907219 and yA=0.972092781. The atom amount stays 2 mol and Q=33.8609295.')
 d.head('F1-F3. Read, export and restore')
 d.p('For 12C, select <b>van ’t Hoff · constant ΔH°</b>, T=400 K and P=100 kPa. Keep Tref=350 K and Cp=0. The direct and formation Gibbs energies supplied at 350 K are unavailable at 400 K because no new point property has been provided.')
 d.p('Use <b>Restore calculator study JSON</b> with your 12A file. It restores and recalculates automatically. Recovered settings should include 350 K, 100 kPa, direct Gibbs source and Cp=0. The expected fresh result is K=3.953263 and ξ=0.705026 mol.')
 d.p('12A→12B changes the composition-dependent Q relation through pressure while K is unchanged. 12A→12C changes the standard Gibbs energy and K through the specified temperature law. Both comparisons retain the same reaction, standard states and initial inventory.','small')
 d.head('G. Exit ticket and feedback')
 d.p('Give your own explanation and one numerical check, with units and conditions. Report actual time and one exact unresolved step if any. Submit once and wait for the receipt. Keep corrections and exported studies for the classroom discussion on 13 November. No additional required assignment follows.','small')
 d.finish()

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'output/pdf');args=ap.parse_args()
 args.output.mkdir(parents=True,exist_ok=True)
 practice(args.output);guide(args.output);solutions(args.output)
