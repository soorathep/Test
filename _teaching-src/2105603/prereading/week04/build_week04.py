"""Rebuild the three English Week 4 handouts using research Python.

Run with --output <directory>. This script contains the complete teaching text.
"""
from pathlib import Path
import argparse
import os
import tempfile
from xml.sax.saxutils import escape

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'week04-matplotlib'))
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
EXIT='https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=4'
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
  self.c.setFont('Bold',8.4);self.c.drawString(M,H-35,'2105603  /  WEEK 04  /  '+self.label.upper())
  self.c.setFillColor(C['graphite']);self.c.setFont('Body',7.5)
  self.c.drawString(M,27,'Advanced Chemical Engineering Thermodynamics | Independent ECS replacement lesson')
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
 doc.p('<b>Session 4 exit ticket + feedback</b>','small',width=CW-111,x=M+111)
 doc.p('Scan the QR or use the clickable link below. The form is anonymous. It is not an attendance-identification form.','small',width=CW-111,x=M+111)
 doc.p(f'<link href="{escape(EXIT)}" color="{skh.C["teal"]}"><u>Open the Session 4 form</u></link>','small',width=CW-111,x=M+111)
 doc.y=min(doc.y,top-size-7)

def practice(output):
 d=Doc(output/'week04-practice.pdf','Week 4 practice: Solid equilibria and adsorption',6,'Practice record')
 d.page('Identify the process and constraints','Page 1 | A and B | Pause at slides 4 (8 min) and 8 (6 min). Keep attempts and corrections separately.')
 d.p('Start at <link href="'+BASE+'week04-study.html"><u>week04-study.html</u></link>. This independent lesson replaces class while the instructor attends the ECS meeting. Watch the integrated opening at the start of the video. Pause for 4 minutes at Opening 13 to write R1-R3 in your notebook; check at Opening 14. Then follow core slides 1-40 with this worksheet. The written opening is an alternative or reference, not extra required reading. Open the Lab guide only when directed. Add 104 minutes of required work and a 10-minute break to the combined recording. H1-H4 are optional; the opening replaces their former required allocation.','small')
 d.head('A. What process are you describing?')
 q(d,'A1.','Classify: (i) a pure solid dissolves into a liquid mixture, (ii) volatile solid enters the gas phase in a sealed vessel, (iii) gas molecules accumulate on an adsorbent surface. Name SLE, bulk GSE or adsorption, and identify the phases involved.',2)
 q(d,'A2.','Week 3 compared liquid states at fixed T and P. Which equilibrium potential is appropriate for a closed, rigid vessel at fixed T and free gas volume? State the conserved amount and explain why pressure is now an output.',2)
 q(d,'A3.','Predict whether adding inert gas at fixed T and V changes the volatile partial pressure while solid remains. Does the same answer apply to total pressure? State the ideal-gas assumption.',2)
 d.head('B. One pure-solid solubility calculation')
 d.p('For a present pure solid i, use ln(xᵢγᵢ)=−(ΔH<sub>fus,i</sub>/R)(1/T−1/T<sub>m,i</sub>). Set R=8.314462618 J mol⁻¹ K⁻¹, T<sub>m</sub>=350 K, ΔH<sub>fus</sub>=10000 J/mol and T=300 K. Assume constant fusion enthalpy, negligible fusion heat-capacity correction and ideal liquid (γᵢ=1).','small')
 q(d,'B1.','Substitute the values, calculate ln xᵢ and then xᵢ. Keep the sign and units explicit.',2)
 q(d,'B2.','Is xᵢ a phase fraction or a composition in the saturated liquid? Can it determine how many moles of solid remain without an inventory balance? Explain what changes when γᵢ is not 1.',2)
 d.p('This is one liquidus relation below the pure-component melting point, not a complete binary phase diagram. Pure-solid activity is 1 only for a present pure solid on its own standard state; its liquid-reference activity need not be 1.','small')
 d.page('Check a finite gas-solid inventory','Page 2 | C1-C3 | Slide 13: 10-minute independent attempt before the numerical check.')
 d.head('C. New volume and sublimation pressure')
 d.p('A synthetic volatile solid and an ideal gas share a closed vessel at T=300 K, free gas volume V=2.00 L and sublimation pressure P<sub>sub</sub>=8.00 kPa. Compare volatile inventories n<sub>A</sub>=0.0100 mol and 0.00400 mol. Initially there is no inert gas. Use R=8.314462618 kPa L mol⁻¹ K⁻¹.')
 d.p('n<sub>cap</sub>=P<sub>sub</sub>V/(RT); n<sub>gas</sub>=min(n<sub>A</sub>,n<sub>cap</sub>); n<sub>solid</sub>=n<sub>A</sub>−n<sub>gas</sub>; P<sub>A</sub>=n<sub>gas</sub>RT/V.','eq')
 q(d,'C1.','Calculate ncap. Complete the table and check nA=ngas+nsolid for both inventories. Explain why PA=Psub is conditional on a solid phase remaining.',3)
 d.table([['nA / mol','ngas / mol','nsolid / mol','PA / kPa','Present phases'],['0.0100','<br/>','<br/>','<br/>','<br/>'],['0.00400','<br/>','<br/>','<br/>','<br/>']],widths=[75,100,100,90,CW-365])
 q(d,'C2.','Add ninert=0.00100 mol at the same T and free volume to each case. Calculate Pinert and Ptotal. Do ngas, nsolid or PA change? Do not replace PA by Ptotal in the sublimation condition.',3)
 q(d,'C3.','For each case, evaluate ln(PA/Psub)=(μgas−μsolid)/(RT) using a hypothetical pure-solid reference. Explain why a negative result with no solid left is not a failed equilibrium calculation. What happens if nA equals ncap exactly?',3)
 d.p('Scope: a pure volatile solid, ideal gases, fixed free gas volume, no chemical reaction, no adsorption, and a specified valid sublimation-pressure relation. A numerical balance does not validate these assumptions for a real substance.','small')

 d.page('Investigate Lab 10 independently','Page 3 | D1: 5-minute prediction at slide 15. Watch slide 16. D2-D4: 22-minute rerun at slide 18.')
 d.link('Open Lab 10: Solid equilibria','labs/solids.html#so-experiment')
 d.head('D1. Predict before the demonstration')
 d.p('Use T=300 K, V=1 L, Tref=300 K, Pref=10 kPa, ΔHsub=50000 J/mol and the declared T range 250-350 K. Predict the cases below before watching slide 16. These are synthetic definitions, not real property data.','small')
 d.table([['Case','nA / mol','ninert / mol','Your phase / pressure prediction'],['10A','0.010','0','<br/>'],['10B','0.002','0','<br/>'],['10C','0.002','0.002','<br/>']],widths=[55,72,90,CW-217])
 d.head('D2. Reproduce three cases')
 d.p('Follow guide pages 1-2. Select <b>GSE · sublimation in a rigid vessel</b>, confirm every input above and calculate. Change only inventory from 10A to 10B, then only inert gas from 10B to 10C. Calculate again after each change. Record unrounded JSON values if a tight balance needs more precision.','small')
 d.table([['Case','PA / Ptotal (kPa)','ngas / nsolid (mol)','Present phases / balance residual'],['10A','<br/>','<br/>','<br/>'],['10B','<br/>','<br/>','<br/>'],['10C','<br/>','<br/>','<br/>']],widths=[55,141,147,CW-343])
 q(d,'D3.','Independently calculate ncap and check all three balances. Inspect both pressure and amount plots: identify temperature on the horizontal axis, the declared range, and the condition where actual partial pressure stops following Psub. Annotate one plot, including its case and axes.',2)
 q(d,'D4.','Export each study and save a comparison. Reopen its JSON in Study workspace, restore a case, verify its settings and recalculate. Compare the fresh result with your record. Explain one corrected prediction, one assumption and why equal chemical potentials need not be imposed on an absent solid.',2)
 d.p('Keep the prediction table, results, hand balance, annotated plot and three exports. Export saves locally; it does not submit work. Use guide page 2 if a result disappears after changing inputs or restoring a case. Then take the 10-minute break at slide 20.','small')

 d.page('Calculate uptake and predict a vessel','Page 4 | E1-E3: slide 25, 10 min. F1-F3: slide 29, 5 min. Predict before the Lab 11 demonstration.')
 d.head('E. Henry and Langmuir at the same temperature')
 d.p('At T=300 K, qs=2 mol/kg and b=0.1 kPa⁻¹. Langmuir: q=qs bP/(1+bP). Its matched low-pressure Henry coefficient is KH=qs b=0.2 mol kg⁻¹ kPa⁻¹, with qH=KH P. P is adsorbate partial pressure and q is absolute uptake per kg of adsorbent.','small')
 q(d,'E1.','Calculate qLangmuir and qHenry at P=5 and 40 kPa. Include units and surface coverage θ=qLangmuir/qs.',1)
 d.table([['P / kPa','Langmuir q / mol kg⁻¹','Henry q / mol kg⁻¹','θ'],['5','<br/>','<br/>','<br/>'],['40','<br/>','<br/>','<br/>']],widths=[63,166,166,CW-395])
 q(d,'E2.','Compare bP with 1 in both cases. Why does matching the zero-pressure slope not make the models interchangeable at these pressures?',1)
 q(d,'E3.','Predict each model as P increases without bound. Does a Langmuir fit alone prove homogeneous sites or a specific adsorption mechanism?',1)
 d.head('F. A worked balance, then a new prediction')
 d.p('Worked example (slide 28): Langmuir qs=2, b=0.1, T=300 K, Vg=1 L, ms=10 g=0.010 kg and specified P=10 kPa. q=1 mol/kg, ngas=PVg/(RT)=0.00400908 mol, nads=msq=0.0100 mol, so nA=0.01400908 mol. This known-pressure example is <b>not</b> the next Lab inventory.','small')
 q(d,'F1.','For Lab 11, keep those parameters but set nA=0.0100 mol, no inert gas. Predict whether the equilibrium P is below or above 10 kPa. Explain using the worked balance, without solving yet.',1)
 q(d,'F2.','Predict how replacing Langmuir with the matched Henry model changes P at this fixed total inventory. Explain the gas-plus-adsorbed balance.',1)
 q(d,'F3.','For Langmuir, double adsorbent mass from 10 to 20 g at fixed nA,T,Vg. Predict the pressure direction. Distinguish uptake per kg from total adsorbed moles.',1)
 d.p('Watch slide 30 after writing the three predictions. Use absolute adsorption and accessible free gas volume in nA=PVg/(RT)+msq(P); excess uptake cannot be substituted without its volume/basis correction.','small')

 d.page('Investigate Lab 11 independently','Page 5 | Slide 32: 24-minute independent rerun | Use Lab guide pages 3-4.')
 d.link('Open Lab 11: Adsorption equilibrium','labs/adsorption.html#ad-experiment')
 d.head('G1. Establish a reproducible model study')
 d.p('Use the <b>Explore isotherms</b> controls, not the fitting section. Synthetic definitions at 300 K: qs=2 mol/kg, b=0.1 kPa⁻¹, Henry K=0.2 mol kg⁻¹ kPa⁻¹. Set plotted pressure range 0-100 kPa, free volume 1 L, total adsorbate 0.0100 mol, inert gas 0 and adsorbent mass 10 g. Keep other model parameters at their synthetic defaults; Freundlich and BET are optional comparisons, not required fitted models.','small')
 d.p('Calculate <b>11A: Langmuir / 10 g</b>. Save it. For <b>11B</b>, change only the selected vessel model to Henry, calculate and save. Return to Langmuir and change only the mass to 20 g for <b>11C</b>; calculate and save.','small')
 d.table([['Case','PA / kPa','q / mol kg⁻¹','ngas / mol','nads / mol'],['11A: Langmuir, 10 g','<br/>','<br/>','<br/>','<br/>'],['11B: Henry, 10 g','<br/>','<br/>','<br/>','<br/>'],['11C: Langmuir, 20 g','<br/>','<br/>','<br/>','<br/>']],widths=[139,75,95,100,CW-409])
 q(d,'G2.','For each case, independently substitute its pressure into q(P), ngas=PVg/(RT), and nads=msq. Verify nA=ngas+nads. Use ms in kg and the same pressure basis as b or KH. Explain any rounding residual.',3)
 q(d,'G3.','Compare each result with F1-F3. Explain why lower q per kg can coexist with more total adsorbed material when mass increases. Annotate the isotherm graph with the low-pressure slope and a finite-pressure departure; a single curve is not a kinetic prediction.',3)
 q(d,'G4.','Export all three model studies, save the comparison JSON, import it into Study workspace, restore one case and recalculate. Check units, model, mass and inventory before comparing the fresh result. Keep one numerical balance, an interpretation and a model limitation with the export.',2)
 d.p('If the vessel result is unavailable, read its message and check whether the equilibrium root lies inside the declared pressure range. Do not substitute a boundary pressure or call an unavailable result zero. Experimental fitting, BET screening and isosteric heat are optional extensions outside this core lesson.','small')

 d.page('Optional transfer and required feedback','Page 6 | H1-H4: optional extension, 20 extra min. I: required, slide 39, 10 min. The opening review replaces required H work.')
 d.head('H. Optional new cases')
 q(d,'H1.','A closed GSE vessel has T=310 K, V=2 L, Psub=5 kPa and no inert gas. For nA=0.002 and 0.008 mol, calculate ncap, ngas, nsolid and PA. Identify the phases and verify each inventory balance.',2)
 q(d,'H2.','Add 0.001 mol inert gas to each H1 case at fixed T,V. Calculate Ptotal and state whether PA changes. Explain which equilibrium condition is an equality while solid is present.',2)
 q(d,'H3.','A synthetic Langmuir model at 310 K has qs=3 mol/kg and b=0.05 kPa⁻¹. At P=20 kPa, Vg=2 L and ms=5 g, calculate q, ngas, nads and the total adsorbate nA needed for that pressure. Show the kg and pressure conversions.',2)
 q(d,'H4.','Keeping the H3 total inventory, T and free gas volume fixed, double adsorbent mass to 10 g. Predict the pressure direction and justify it with the balance; no numerical root is required. Give one assumption shared by the GSE and adsorption calculations and one difference between their physical descriptions.',2)
 d.link('After attempting H1-H4: open worked solutions','files/week04-solutions.pdf')
 d.head('I. Exit ticket, feedback and saved evidence')
 d.p('Use the existing Session 4 form during the 10-minute pause on slide 39. Answer its <b>concept</b> question using the finite solid inventory and partial-pressure condition. In the <b>evidence</b> answer include one Lab 10 comparison and one Lab 11 balance, with settings and units. In the existing feedback text, give your actual study minutes, pacing and any unclear step. Submit once and wait for <b>Response received</b>. On slide 40 verify the receipt and save the worksheet, corrections and exports; do not resubmit.','small')
 qr(d)
 d.finish()
def guide(output):
 d=Doc(output/'week04-lab-guide.pdf','Week 4 Lab guide: Solid equilibria and adsorption',4,'Lab guide')
 d.page('Lab 10: set up a closed GSE vessel','Guide page 1 | Worksheet D, p. 3 | Predict at slide 15, watch slide 16, rerun at slide 18.')
 d.link('Open Lab 10: Solid equilibria','labs/solids.html#so-experiment')
 d.p('The lesson uses the GSE part of Lab 10. The SLE equation is a hand calculation; the binary eutectic interface is optional. Select <b>Experiment → GSE · sublimation in a rigid vessel</b> first, because changing mode resets its synthetic defaults.')
 d.table([['Field','Enter / check'],['Property sources','Synthetic teaching definitions; not experimental properties.'],['Temperature / K','300'],['Minimum / maximum valid T / K','250 / 350'],['Subliming component / inert carrier','Synthetic volatile solid / Synthetic inert gas'],['Fixed free gas volume / L','1'],['Total volatile inventory / mol','0.010 for case 10A'],['Inert gas inventory / mol','0'],['Reference temperature / K','300'],['Sublimation pressure at reference / kPa','10'],['Sublimation enthalpy / J mol⁻¹','50000']],widths=[260,CW-260],padding=5)
 d.p('Click <b>Calculate equilibrium →</b>. Read the phase label and results table. At T=Tref, the supplied sublimation pressure equals Pref. The entered ΔHsub controls the temperature sweep; it does not change Psub at that reference point.')
 d.head('Before changing anything')
 d.p('Record PA, total pressure, volatile gas amount, remaining solid and the balance residual. Use ncap=PsubV/(RT) to check the result independently. Name your run 10A in your worksheet and, if desired, in the workspace field <b>Label for the next captured case</b>.')
 d.p('Select <b>Export study JSON</b>. The file downloads and is also captured in the in-memory workspace. The worksheet is your explanation; the exported study is a reproducible input/result record. Neither is automatically submitted.','small')

 d.page('Lab 10: compare, save and reopen','Guide page 2 | Three controlled cases | Keep the same T, volume, property relation and declared range.')
 d.table([['Case','Change from previous case','Record'],['10A','Start nA=0.010 mol, inert=0','Phase, PA, Ptotal, gas and solid'],['10B','Only nA → 0.002 mol','Same quantities; explain depletion'],['10C','Only inert → 0.002 mol','Separate partial from total pressure']],widths=[52,217,CW-269])
 d.p('After every input change, click <b>Calculate equilibrium →</b> before recording or exporting. The interface clears old results when inputs change. A disabled export button or “Inputs changed” message means the current inputs have no fresh result.')
 d.head('Read both plots')
 d.p('Choose <b>Partial and total pressure</b>, then <b>Gas and solid amounts</b>. The horizontal axis is temperature across the declared range, not time. The selected 300 K result is in the table. Compare actual volatile partial pressure with sublimation pressure; total pressure also includes inert gas. In the amount plot, gas plus solid is the volatile inventory and excludes inert gas.')
 d.p('Where solid remains, PA=Psub. After the solid inventory is exhausted, PA can be lower. A negative (μgas−μsolid)/RT then refers to the hypothetical absent solid and is compatible with stable all-vapor equilibrium. Gaps can indicate a pressure guard; do not interpret a missing segment as zero.')
 d.head('Save and reopen an actual calculation')
 d.p('1. Export each fresh case. Open <b>Study workspace · reopen and compare cases</b> near the top of the page. Check the captured case labels.')
 d.p('2. Click <b>Download comparison</b>. Keep the JSON with your worksheet. It contains records from this Lab only; Lab 11 uses its own comparison file.')
 d.p('3. To verify a saved file, use <b>Load studies or a comparison JSON</b>. If necessary, download first and use <b>Clear comparison</b> to avoid duplicate cases or the eight-case limit. Clearing the in-memory list does not delete downloaded files.')
 d.p('4. Click <b>Restore</b> beside the intended case. Verify the mode, temperature, volume, inventories and property values. Click <b>Calculate equilibrium →</b> again. Compare the fresh result with the recorded values; imported results are evidence, not a fresh solve.')
 d.p('<b>Raw JSON units:</b> Lab 10 stores pressure fields in Pa and volume in m³: input.Pref=10000 means 10 kPa; input.volume=0.001 means 1 L. Workspace controls preserve the values entered in the labeled interface. Do not treat raw-field numbers as display units.','small')
 d.p('Keep one annotated plot, three records and an independent balance. Model assumptions: ideal gases, one pure solid, no adsorption or reaction, fixed free gas volume, and no liquid formation in the declared range.','small')

 d.page('Lab 11: compare uptake models','Guide page 3 | Worksheet E-F, p. 4; G, p. 5 | Predict at slide 29, watch slide 30, rerun at slide 32.')
 d.link('Open Lab 11: Adsorption equilibrium','labs/adsorption.html#ad-experiment')
 d.p('Work in <b>Explore isotherms</b>. Select <b>Reset synthetic parameters</b> if you need the defined starting point. The experimental fitting section below is optional and is not required for this lesson.')
 d.table([['Field','Value'],['Adsorbate / adsorbent','Synthetic gas / Synthetic adsorbent'],['Parameter source','Synthetic definitions at 300 K'],['Parameter and vessel temperature / K','300'],['Minimum / maximum model pressure / kPa','0 / 100'],['Model to edit and use in the vessel','Langmuir initially'],['Capacity qs / mol kg⁻¹','2'],['Affinity b / kPa⁻¹','0.1'],['Henry K / mol kg⁻¹ kPa⁻¹','0.2 (select Henry to inspect/edit)'],['Closed vessel: free gas volume / L','1'],['Dry adsorbent mass / g','10 initially'],['Total adsorbate inventory / mol','0.010'],['Nonadsorbing inert gas / mol','0']],widths=[270,CW-270],padding=5)
 d.p('Expand <b>Closed vessel</b> to inspect its inputs. Return the selected model to Langmuir and click <b>Compare &amp; solve vessel →</b>. The isotherm plot shows all four independently specified models, but the vessel table uses only the selected model.')
 d.p('Pressure is adsorbate partial pressure in kPa. Uptake is absolute mol/kg of dry adsorbent, numerically equal to mmol/g. The interface takes mass in g and volume in L; use kg in your hand balance. Temperature labels supplied parameters; changing T alone does not predict new adsorption parameters.','small')

 d.page('Lab 11: balance and retain evidence','Guide page 4 | Finish G, then submit I; H is optional | No experimental data upload or fitting is required.')
 d.table([['Case','Selected model','Dry mass / g','Other inputs'],['11A','Langmuir','10','Fixed as guide p. 3'],['11B','Henry','10','Only model changes'],['11C','Langmuir','20','Compare with 11A']],widths=[58,126,96,CW-280])
 d.p('For each case, click <b>Compare &amp; solve vessel →</b>, record PA, q, gas adsorbate amount and adsorbed amount, and click <b>Export model study</b>. Input changes invalidate the previous result. Save each completed case before changing a control.')
 d.head('Calculate the independent balance')
 d.p('nA = PA Vg/(RT) + ms q(PA)','eq')
 d.p('Use R=8.314462618 kPa L mol⁻¹ K⁻¹, Vg=1 L and ms=0.010 or 0.020 kg. With no inert gas, total gas pressure equals PA. Check the separate gas and adsorbed amounts, not only the small residual reported by the solver. Rounded display values can create a small hand residual; JSON preserves additional digits.')
 d.p('Matching KH=qs b gives the same zero-pressure slope. It does not make Henry and Langmuir equivalent at finite pressure. For a larger adsorbent mass at fixed total inventory, distinguish lower uptake per kg from the total amount adsorbed on all of the solid.')
 d.head('Reopen and recalculate')
 d.p('Open <b>Study workspace · reopen and compare cases</b>. Download the Lab 11 comparison, then load it through <b>Load studies or a comparison JSON</b>. Restore a chosen case, check the selected model and all vessel inputs, and click <b>Compare &amp; solve vessel →</b> for a fresh solve. Keep the comparison and worksheet together. Do not mix Lab 10 and Lab 11 files in one workspace.')
 d.p('<b>Raw JSON units:</b> Lab 11 stores volume in m³ and adsorbent mass in kg: 0.001 m³=1 L and 0.010 kg=10 g. Its pressure and isotherm parameters retain the labeled kPa basis. Workspace control strings retain the original display units.','small')
 d.head('If a result is unavailable')
 d.p('Read the reported reason. The vessel root must lie inside the declared pressure range and model window. Expand a range only when supported by the model/property source, not merely to force an answer. Absolute and excess uptake have different balances; do not substitute excess adsorption without its correction. No kinetics or energy balance is solved.')
 d.p('H1-H4 on worksheet p. 6 are optional. The video already includes the questions-first opening and its R1-R3 pause; do not add another reading block. Skip to slide 39 for the required form: the existing anonymous Session 4 exit ticket and feedback; include numerical evidence from both Labs and actual study time. Submit once, wait for “Response received,” then verify the receipt on slide 40. No separate attendance identity is collected.','small')
 d.link('Return to the complete lesson route','week04-study.html')
 d.finish()
def solutions(output):
 d=Doc(output/'week04-solutions.pdf','Week 4 worked solutions: Solid equilibria and adsorption',4,'Worked solutions')
 d.page('A-C. Phases, constraints and inventory','Solutions page 1 | Check only after attempting the corresponding worksheet questions. All numerical cases are synthetic.')
 d.head('A. Describe the physical system first')
 d.p('<b>A1.</b> (i) SLE: pure solid plus liquid solution; (ii) bulk GSE: solid plus vapor; (iii) adsorption: gas exchanges molecules with a surface-associated phase, represented by uptake. None of these descriptions requires a chemical reaction. <b>A2.</b> Stable equilibrium minimizes Helmholtz energy at fixed T,V and conserved total amounts. Week 3 used Gibbs energy at fixed T,P. Pressure is an output in the rigid vessel.','small')
 d.p('<b>A3.</b> For ideal gases at fixed T,V, adding nonreacting, nonsorbing inert gas changes total pressure but not volatile partial pressure or the volatile gas/solid amounts. While solid remains, PA=Psub. This conclusion need not hold for a pressure-controlled vessel or a nonideal mixture.','small')
 d.head('B. Saturated liquid composition')
 d.p('ln x = −(10000/8.314462618)(1/300−1/350) = <b>−0.5727255</b>; x = <b>0.5639862</b>. This is a saturated liquid mole fraction, not the liquid phase fraction or remaining solid amount. An inventory balance is needed for amounts. With nonideal liquid, solve xγ=x<sub>ideal</sub> using a stated activity model. The pure solid has unit activity on its own standard state; the subcooled-liquid reference accounts for the fusion free-energy difference.','small')
 d.head('C1-C2. Independent GSE case')
 d.p('At 300 K and V=2 L, Psub=8 kPa gives ncap=8×2/(8.314462618×300)=<b>0.00641452560 mol</b>. Adding 0.001 mol inert gas gives Pinert=<b>1.247169393 kPa</b>.','small')
 d.table([['nA / mol','ngas / mol','nsolid / mol','PA / kPa','Ptotal with inert / kPa'],['0.010','0.006414526','0.003585474','8.000000','9.247169'],['0.004','0.004000000','0','4.988678','6.235847']],widths=[61,105,104,90,CW-360])
 d.p('Both balances recover the supplied volatile inventory. The larger inventory supports solid plus vapor; the smaller gives vapor only. With no inert gas, Ptotal=PA. Adding inert leaves the four volatile quantities unchanged and adds its partial pressure to Ptotal.','small')
 d.head('C3. Equality is conditional on phase presence')
 d.p('For the solid-present case, ln(PA/Psub)=<b>0</b>. For the depleted case, ln(4.988677571/8)≈<b>−0.472271</b>. Moving a hypothetical infinitesimal amount from solid into the gas would lower free energy, but no solid is available. The nonnegative solid-amount constraint is active, so this inequality is compatible with equilibrium.','small')
 d.p('At nA=ncap exactly, the gas is saturated with zero remaining solid. This is the depletion boundary; an infinitesimal excess inventory creates solid without changing PA at the specified T,V. Do not claim a positive solid amount from pressure equality alone.','small')

 d.page('D. Lab 10 evidence and numerical checks','Solutions page 2 | Lab 10 at T=Tref=300 K, V=1 L and Pref=Psub=10 kPa. ΔHsub=50000 J/mol.')
 d.p('The capacity is ncap=10/(8.314462618×300)=<b>0.004009078501 mol</b>. The 250-350 K declared correlation range is retained for the plots. These synthetic properties are not assigned to a real substance.')
 d.table([['Case','10A','10B','10C'],['nA / mol','0.010','0.002','0.002'],['ninert / mol','0','0','0.002'],['ngas / mol','0.004009079','0.002','0.002'],['nsolid / mol','0.005990921','0','0'],['PA / kPa','10.000000','4.988678','4.988678'],['Ptotal / kPa','10.000000','4.988678','9.977355'],['Present phases','Solid + vapor','Vapor only','Vapor only']],widths=[158,117,117,CW-392])
 d.head('D1-D3. Interpret the controlled changes')
 d.p('From 10A to 10B, the inventory drops below ncap. All 0.002 mol are in the gas, so PA=nART/V=<b>4.988677571 kPa</b>, below Psub. From 10B to 10C, the added inert gas contributes another <b>4.988677571 kPa</b>. PA remains unchanged; Ptotal becomes <b>9.977355142 kPa</b>.')
 d.p('An independent balance gives 0.004009078501+0.005990921499=0.010 for 10A, and 0.002+0=0.002 for 10B/10C. The inert gas belongs in its own balance, not in the volatile gas-plus-solid sum.')
 d.p('The plots vary temperature at fixed specified inventories and free gas volume. While solid remains, actual partial pressure follows Psub(T). Once the finite inventory is entirely gaseous, PA follows nART/V. The amount plot transfers inventory between gas and solid while preserving their sum. Plot gaps can reflect the pressure guard rather than a physical discontinuity.')
 d.head('D4. What a useful saved record contains')
 d.p('Keep the original prediction, model/property definitions, T,V, inventories, phase label, pressures, amount balance and one annotated plot. A JSON file preserves numerical evidence and controls. Restoring controls does not itself establish a current result: verify inputs and click <b>Calculate equilibrium →</b>.')
 d.p('A correct balance and equality while solid is present verify the admitted teaching model. They do not establish real-property accuracy, kinetics, a solid-solution model, adsorption behavior or the absence of liquid formation outside the declared conditions.')

 d.page('E-G. Uptake and closed-vessel balance','Solutions page 3 | T=300 K; qs=2 mol/kg, b=0.1 kPa⁻¹ and matched Henry K=0.2 mol kg⁻¹ kPa⁻¹.')
 d.table([['P / kPa','Langmuir q / mol kg⁻¹','Henry q / mol kg⁻¹','Langmuir θ'],['5','0.6666667','1.000000','0.3333333'],['40','1.600000','8.000000','0.8000000']],widths=[62,166,167,CW-395])
 d.p('<b>E2-E3.</b> bP=0.5 and 4, so neither is the asymptotic bP≪1 limit. KH=qs b matches the initial slope, not the full curve. Langmuir approaches qs=2 mol/kg; Henry increases without bound and is a low-pressure approximation. Model agreement with observations alone does not prove a microscopic site mechanism.','small')
 d.head('F. Known-pressure example and predictions')
 d.p('At P=10 kPa, Langmuir q=1 mol/kg. With V=1 L and ms=0.010 kg, ngas=<b>0.004009078501 mol</b> and nads=<b>0.010000 mol</b>, requiring nA=<b>0.014009078501 mol</b>. Lab 11 instead uses 0.010 mol total, so F1 predicts P&lt;10 kPa. At positive P the matched Henry model gives more uptake than Langmuir, so F2 predicts a lower closed-vessel pressure. Adding more adsorbent at fixed inventory lowers P in F3.','small')
 d.head('G1-G2. Actual Lab 11 cases, nA=0.010 mol')
 d.table([['Case','P / kPa','q / mol kg⁻¹','ngas / mol','nads / mol'],['11A: Langmuir / 10 g','6.080248','0.7562381','0.002437619','0.007562381'],['11B: Henry / 10 g','4.165091','0.8330182','0.001669818','0.008330182'],['11C: Langmuir / 20 g','2.844978','0.4429713','0.001140574','0.008859426']],widths=[134,83,96,98,CW-411])
 d.p('For 11A: q=2(0.1×6.080247972)/(1+0.1×6.080247972)=0.7562380857 mol/kg. ngas=6.080247972/(8.314462618×300)=0.002437619143 mol; nads=0.010×0.7562380857=0.007562380857 mol. Their sum is 0.010000000000 mol. The same substitutions close 11B/11C; use 0.020 kg in 11C.','small')
 d.p('<b>G3.</b> Doubling mass lowers pressure and q per kg, but increases total adsorbed moles from 0.00756238 to 0.00885943 mol because there are more kg of adsorbent. The gas amount correspondingly falls. These fixed-T equilibrium models give no uptake rate or thermal transient.','small')
 d.p('<b>G4.</b> Save each model study and a Lab 11 comparison JSON. After importing and restoring, verify model, parameters, mass, inventory and pressure units, then click <b>Compare &amp; solve vessel →</b>. Report unavailable roots as unavailable, not zero; do not extrapolate merely to obtain a numerical answer.','small')

 d.page('H-I. Optional new cases and reflection','Solutions page 4 | H1-H4 are optional extension work. Open these answers after an optional independent attempt.')
 d.head('H1-H2. A new GSE vessel')
 d.p('At T=310 K, V=2 L and Psub=5 kPa, ncap=10/(8.314462618×310)=<b>0.003879753388 mol</b>. For 0.001 mol inert gas, Pinert=<b>1.288741706 kPa</b>.','small')
 d.table([['nA / mol','ngas / mol','nsolid / mol','PA / kPa','Ptotal with inert / kPa'],['0.002','0.002000000','0','2.577483','3.866225'],['0.008','0.003879753','0.004120247','5.000000','6.288742']],widths=[61,106,105,89,CW-361])
 d.p('The first case is vapor only and undersaturated; the second contains solid plus vapor with PA=Psub. Adding ideal inert gas at fixed free volume changes only total pressure. Equal chemical potentials are required between phases that coexist, while the absent-solid case obeys the appropriate inequality.','small')
 d.head('H3. A new known-pressure adsorption case')
 d.p('At P=20 kPa, bP=0.05×20=1. Thus q=3×1/(1+1)=<b>1.5 mol/kg</b>. At T=310 K and Vg=2 L: ngas=20×2/(8.314462618×310)=<b>0.015519013554 mol</b>.')
 d.p('With ms=5 g=<b>0.005 kg</b>, nads=0.005×1.5=<b>0.0075 mol</b>. The required total inventory is nA=0.015519013554+0.0075=<b>0.023019013554 mol</b>. The matched Henry slope would be qs b=0.15 mol kg⁻¹ kPa⁻¹, but the requested calculation uses Langmuir.')
 d.head('H4. Direction without solving a new root')
 d.p('At the old pressure, doubling mass doubles msq while the gas term stays fixed, exceeding the fixed total inventory. Both gas amount and Langmuir uptake increase monotonically with pressure, so the new equilibrium pressure must be <b>lower</b>. A numerical root is not required. Uptake per kg falls, while total adsorbed amount rises as the gas amount decreases.')
 d.p('Both teaching calculations use ideal gas and fixed T/free volume with an inventory balance. Bulk sublimation relates a present pure solid to vapor through Psub; adsorption uses a surface uptake relation and the mass of adsorbent. Neither model predicts reaction equilibrium or kinetics.')
 d.head('I. Report evidence and actual study time')
 d.p('Use the Session 4 concept question for the finite-inventory/partial-pressure explanation. Include one Lab 10 comparison and one Lab 11 numerical balance in the evidence answer. Add actual minutes, pacing and a remaining question in feedback. Submit once at slide 39 and wait for “Response received”; verify the receipt and save your work at slide 40. The anonymous form does not identify individual attendance.','small')
 d.link('Return to the lesson and Session 4 form','week04-study.html#exit')
 d.finish()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 for build in (practice,guide,solutions):build(args.output)
