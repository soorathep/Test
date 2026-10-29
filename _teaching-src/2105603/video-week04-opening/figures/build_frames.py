"""Regenerate the opening video frames and the complete matching PDF.

Use the absolute research interpreter. Original core PDF pages are reused;
core 2, 3, 35 and 36 are replaced to match the optional H route. These are
video teaching frames, not a PowerPoint artifact. No student data are read.
"""
from pathlib import Path
import io,json,os,html
os.environ.setdefault("MPLCONFIGDIR","/private/tmp/week04-opening-matplotlib")
import skh_palette as skh
skh.use()
from matplotlib.font_manager import findfont,FontProperties
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pymupdf
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
SRC=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/week04-opening-video"
SITE=Path.home()/"Documents/GitHub/Test"
W,H=960,540;M=54
C={k:colors.HexColor(v) for k,v in skh.C.items()}
for name,fam,weight in [("Body","DejaVu Sans","normal"),("Bold","DejaVu Sans","bold"),("Title","DejaVu Serif","bold")]:
 pdfmetrics.registerFont(TTFont(name,findfont(FontProperties(family=fam,weight=weight))))
pdfmetrics.registerFontFamily("Body",normal="Body",bold="Bold",italic="Body",boldItalic="Bold")
ST={"title":ParagraphStyle("title",fontName="Title",fontSize=30,leading=36,textColor=C["graphite"]),"body":ParagraphStyle("body",fontName="Body",fontSize=20,leading=27,textColor=C["graphite"]),"eq":ParagraphStyle("eq",fontName="Body",fontSize=22,leading=31,textColor=C["graphite"]),"small":ParagraphStyle("small",fontName="Body",fontSize=14,leading=20,textColor=C["graphite"]),"table":ParagraphStyle("table",fontName="Body",fontSize=17,leading=23,textColor=C["graphite"])}

class Frame:
 def __init__(self,title,label):
  self.buffer=io.BytesIO();self.c=canvas.Canvas(self.buffer,pagesize=(W,H),initialFontName="Body",pageCompression=1)
  self.c.setTitle(title);self.c.setAuthor("2105603 | SKH Research Group")
  self.c.setFillColor(C["teal"]);self.c.rect(0,H-5,W,5,fill=1,stroke=0)
  self.c.setFont("Bold",10);self.c.drawString(M,H-27,"2105603 / WEEK 4 / "+label.upper())
  self.c.setFillColor(C["graphite"]);self.c.setFont("Body",10);self.c.drawString(M,17,"Questions, calculations and evidence | English narrated lesson")
  self.y=H-50;self.p(title,"title",gap=16)
  self.c.setStrokeColor(C["teal"]);self.c.line(M,self.y+6,W-M,self.y+6)
  self.figure_box=None
 def p(self,text,kind="body",gap=12,x=M,width=W-2*M):
  p=Paragraph(text,ST[kind]);_,h=p.wrap(width,H)
  assert self.y-h>38,(text,self.y,h)
  p.drawOn(self.c,x,self.y-h);self.y-=h+gap
 def table(self,table,width=W-2*M):
  headers=table["headers"];rows=[headers]+table["rows"]
  widths=table.get("widths") or [width/len(headers)]*len(headers)
  t=Table([[Paragraph(str(v),ST["table"]) for v in row] for row in rows],colWidths=widths)
  t.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"Body"),("BACKGROUND",(0,0),(-1,0),C["paper"]),("LINEBELOW",(0,0),(-1,0),1,C["teal"]),("LINEBELOW",(0,1),(-1,-1),.5,C["mist"]),("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9)]))
  _,h=t.wrap(width,H);assert self.y-h>40,("table overflow",self.y,h)
  t.drawOn(self.c,M,self.y-h);self.y-=h+14
 def finish(self):
  self.c.showPage();self.c.save();doc=pymupdf.open(stream=self.buffer.getvalue(),filetype="pdf")
  if self.figure_box:
   image=pymupdf.open(SITE/"teaching/2105603/figures/gibbs-review-curve.pdf")
   doc[0].show_pdf_page(self.figure_box,image,0)
  return doc

def draw(entry):
 d=entry["display"];f=Frame(entry["title"],"Opening "+entry["id"])
 if d.get("kicker"):f.p(d["kicker"],"small",gap=12)
 if d.get("figure"):
  f.figure_box=pymupdf.Rect(38,H-f.y,622,H-48)
  y=f.y
  for line in d.get("bullets",[]):f.p(line,"small",x=646,width=262,gap=15)
  for line in d.get("equations",[]):f.p(line,"small",x=646,width=262,gap=10)
 else:
  for line in d.get("equations",[]):f.p(line,"eq",gap=10)
  if d.get("table"):f.table(d["table"])
  for line in d.get("bullets",[]):f.p(line,"body",gap=14)
 for key in ("callout","footer","note"):
  if d.get(key):
   if d.get("figure"):f.p(d[key],"small",x=646,width=262,gap=8)
   else:f.p(d[key],"small",gap=8)
 return f.finish()

def patch(n):
 if n==2:
  f=Frame("Your independent lesson","Core slide 02")
  f.p("Keep your first answers, then add corrections after each check.","body")
  base="https://www.skhgroup.net/teaching/2105603/"
  f.p('<link href="'+base+'files/week04-practice.pdf" color="'+skh.C["teal"]+'"><u>Practice worksheet · 6 pages</u></link><br/>Complete A–G and I. H1–H4 is optional.',"body")
  f.p('<link href="'+base+'files/week04-lab-guide.pdf" color="'+skh.C["teal"]+'"><u>Lab guide · 4 pages</u></link><br/>Use the named settings, controls and interpretation checks.',"body")
  f.p('<link href="'+base+'files/week04-solutions.pdf" color="'+skh.C["teal"]+'"><u>Worked solutions</u></link><br/>Open the relevant answer only after your own attempt.',"body")
  f.p("Predict before the Lab 10 and Lab 11 demonstrations. Then repeat independently and retain your calculations and study JSON.","small")
 elif n==3:
  f=Frame("The study route","Core slide 03")
  f.p("Opening review completed: keep your R1–R3 answers.","small")
  f.table({"headers":["Next action","Worksheet"],"widths":[650,202],"rows":[["Processes, solubility and finite inventory","pp. 1–2, A–C"],["Predict, watch and investigate Lab 10","p. 3, D"],["Take a 10-minute break",""],["Adsorption calculations and Lab 11","pp. 4–5, E–G"],["Submit exit ticket and feedback once","p. 6, I"]]})
  f.p("Required: full recording + 104 min of work + 10 min break.<br/>H1–H4 is optional (+20 min). No second required reading.","small")
 elif n==35:
  f=Frame("Optional transfer practice","Core slide 35")
  f.p("H1–H4 on worksheet p. 6 is optional. It adds about 20 minutes.","body")
  f.p("Required route: go to core slide 39 for section I and the form.","body")
  f.p("If you choose H: use new gas–solid and adsorption parameters. Keep the worked solutions closed until your attempt.","body")
  f.p("For the exact case values, use worksheet p. 6. Apply the same inventory balances, units and phase-presence checks.","body")
 elif n==36:
  f=Frame("Choose your route","Core slide 36")
  f.p("<b>Required route:</b> select “Go to exit ticket (slide 39)”. Complete I and submit the Session 4 form once.","body")
  f.p("<b>Optional extension:</b> pause for about 20 minutes to attempt H1–H4, then continue to its check.","body")
  f.p("H: gas capacity → phase amounts → partial and total pressure.<br/>Adsorption: uptake → gas and adsorbed moles → inventory.","body")
  f.p("Use the worksheet case values. The opening review has replaced H in the required lesson budget.","small")
 else:raise ValueError(n)
 return f.finish()

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 entries=json.loads((SRC/"opening-draft.json").read_text());entries=entries.get("slides",entries) if isinstance(entries,dict) else entries
 assert len(entries)==14
 result=pymupdf.open();changed=[]
 for e in entries:
  doc=draw(e);result.insert_pdf(doc);changed.append((int(e["id"]),"opening-"+e["id"]))
 with pymupdf.open(SRC/"base-core-slides.pdf") as old:
  assert len(old)==40
  for i in range(40):
   if i+1 in [2,3,35,36]:result.insert_pdf(patch(i+1));changed.append((14+i+1,"core-"+str(i+1)))
   else:result.insert_pdf(old,from_page=i,to_page=i)
 result.set_metadata({"title":"Week 4 video frames: Questions, solid equilibria and adsorption","author":"Soorathep Kheawhom","subject":"Integrated narration edition; R1–R3 then A–G and I; H optional"})
 target=OUT/"week04-video-slides.pdf";result.save(target,garbage=4,deflate=True)
 preview=OUT/"frames-qa";preview.mkdir(exist_ok=True)
 sheet=Image.new("RGB",(960,270*((len(changed)+1)//2)),"white");dr=ImageDraw.Draw(sheet)
 for k,(page,label) in enumerate(changed):
  p=result[page-1];pix=p.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
  img=Image.frombytes("RGB",(pix.width,pix.height),pix.samples);img.save(preview/f"{label}.png")
  img.thumbnail((480,270));sheet.paste(img,((k%2)*480,(k//2)*270))
 sheet.save(preview/"contact-sheet.png")
 # All new and changed text must stay on its PDF page.
 for page,_ in changed:
  p=result[page-1]
  for b in p.get_text("dict")["blocks"]:
   if "lines" not in b:continue
   for line in b["lines"]:
    for s in line["spans"]:
     r=pymupdf.Rect(s["bbox"]);assert r.x0>=0 and r.y0>=0 and r.x1<=p.rect.width+.1 and r.y1<=p.rect.height+.1,(page,s["text"])
 print(target, "54 pages; 18 new/revised frames rendered; text bounds passed")
if __name__=="__main__":main()
