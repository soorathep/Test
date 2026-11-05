"""Read-only Week 5 release inspection. Writes only its local audit receipt."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,unquote
import hashlib,json,math,re,subprocess
import pymupdf
from bs4 import BeautifulSoup
HOME=Path.home()
SITE=HOME/'.codex/worktrees/week05-video/Test'
COURSE=SITE/'teaching/2105603'
SOURCE=SITE/'_teaching-src/2105603/video-week05'
TASK=HOME/'Documents/Projects/Adv thermo/asynchronous-week05'
OUTPUT=TASK/'qa/release-audit.json'
checks=[];issues=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def record(name,passed,details):
 checks.append({'check':name,'passed':bool(passed),'details':details})
 if not passed:issues.append(name)
def rel(p):return str(p.relative_to(SITE))
def git(*args):return subprocess.check_output(['git','-C',str(SITE),*args]).decode()
state=git('status','--porcelain=v1','--untracked-files=all','-z')
changed=[r[3:] for r in state.split('\0') if r]
record('Changes scoped to course 2105603',all(p.startswith(('teaching/2105603/','_teaching-src/2105603/')) for p in changed),{'count':len(changed),'outside_scope':[p for p in changed if not p.startswith(('teaching/2105603/','_teaching-src/2105603/'))]})
contract=json.loads((SOURCE/'documents/lesson-contract.json').read_text())
narration=json.loads((SOURCE/'media/narration.json').read_text())
timeline=json.loads((SOURCE/'qa/timeline.json').read_text())
manifest=json.loads((SOURCE/'qa/audio-manifest.json').read_text())
player=BeautifulSoup((COURSE/'week05-video.html').read_text(),'html.parser')
study=BeautifulSoup((COURSE/'week05-study.html').read_text(),'html.parser')
chapters=json.loads(player.select_one('#chapter-data').text)
record('32 chapters align across contract, narration, audio and player',len(chapters)==len(contract['slides'])==len(narration)==len(manifest)==len(timeline['slides'])==32,{'chapter_count':len(chapters)})
metadata=[]
for i,(c,n,m,t,p) in enumerate(zip(contract['slides'],narration,manifest,timeline['slides'],chapters),1):
 valid=c['number']==n['slide']==m['slide']==t['slide']==p['slide']==i and c['id']==n['slide_id']==m['slide_id']==t['slide_id']==p['slide_id'] and c['title']==n['title']==m['title']==t['title']==p['title'] and c['pause_minutes']==n['activity_minutes']==m['activity_minutes']==t['activity_minutes']==p['activity_minutes'] and n['narration']==m['narration']==p['narration'] and abs(t['start_seconds']-p['start'])<1e-8 and abs(t['end_seconds']-p['end'])<1e-8
 metadata.append({'slide':i,'id':c['id'],'valid':valid})
record('Exact titles, IDs, spoken script, pause budgets and player times match',all(r['valid'] for r in metadata),metadata)
breakmin=sum(c['activity_minutes'] for c in chapters if c['is_break']);workmin=sum(c['activity_minutes'] for c in chapters if not c['is_break']);duration=chapters[-1]['end'];total=duration/60+workmin+breakmin
record('Required workload is approximately three hours',workmin==128 and breakmin==10 and abs(duration-2487.4780416666667)<1e-8 and 178<total<181,{'recording_seconds':duration,'work_minutes':workmin,'break_minutes':breakmin,'total_minutes':total,'activity_stops':sum(c['activity'] for c in chapters)})
record('Measured timing appears in student pages',all('41:27' in s.get_text() and '179.5' in s.get_text() for s in [player,study]),{'displayed_recording':'41:27','displayed_total_minutes':179.5})
deck=BeautifulSoup((COURSE/'postmidterm-05.html').read_text(),'html.parser')
ids=[s.get('id') for s in deck.select('.slides > section')]
record('Slide deck has the same 32 chapter IDs',ids==[c['id'] for c in contract['slides']],{'deck_ids':ids})
pdfs={
'files/postmidterm-05-slides.pdf':32,
'files/week05-practice.pdf':6,
'files/week05-lab-guide.pdf':2,
'files/week05-solutions.pdf':5,
}
pdfinfo=[]
for name,count in pdfs.items():
 p=COURSE/name
 with pymupdf.open(p) as d:
  fonts={x[2] for page in d for x in page.get_fonts()}
  actual=len(d)
 emb=subprocess.check_output(['pdffonts',str(p)]).decode()
 rows=emb.splitlines()[2:]
 no_type3='Type 3' not in emb
 all_embedded=all(re.search(r'\byes\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$',line) for line in rows)
 pdfinfo.append({'file':name,'expected_pages':count,'pages':actual,'font_types':sorted(fonts),'no_type3':no_type3,'all_fonts_embedded':all_embedded,'sha256':sha(p)})
record('PDF counts and embedded fonts',all(x['pages']==x['expected_pages'] and x['no_type3'] and x['all_fonts_embedded'] for x in pdfinfo),pdfinfo)
record('Public slide PDF equals reviewed video input',sha(COURSE/'files/postmidterm-05-slides.pdf')==timeline['source_pdf_sha256']==sha(SOURCE/'reviewed-slides.pdf'),{'sha256':timeline['source_pdf_sha256']})
missing=[];badanchors=[];urlchecks=[];external=set();parsecache={}
def checkurl(page,url):
 if not url or url.startswith(('data:','mailto:','tel:','javascript:')):return
 config=(SITE/'_config.yml').read_text()
 base=re.search(r'^baseurl:\s*\"([^\"]*)\"',config,re.M)
 assert base is not None, 'Expected explicit quoted Jekyll baseurl.'
 url=url.replace('{{ site.baseurl }}',base.group(1))
 u=urlsplit(url)
 if u.scheme or u.netloc:
  external.add(url)
  if u.netloc!='www.skhgroup.net':return
  target=SITE/unquote(u.path.lstrip('/'))
 else:
  target=SITE/unquote(u.path.lstrip('/')) if u.path.startswith('/') else page.parent/unquote(u.path)
 if not u.path:target=page
 if target.is_dir():target=target/'index.html'
 if not target.exists():missing.append({'page':rel(page),'url':url,'target':rel(target)});return
 if u.fragment and target.suffix.lower()=='.html':
  if target not in parsecache:parsecache[target]=BeautifulSoup(target.read_text(),'html.parser')
  soup=parsecache[target];fragment=u.fragment.lstrip('/')
  dynamic=[]
  cdata=soup.select_one('#chapter-data')
  if cdata:dynamic=[x['anchor'] for x in json.loads(cdata.text)]
  if not soup.find(id=fragment) and not soup.find(attrs={'name':fragment}) and fragment not in dynamic:
   badanchors.append({'page':rel(page),'url':url,'fragment':fragment})
 urlchecks.append({'page':rel(page),'url':url})
for name in ['week05-video.html','week05-study.html']:
 page=COURSE/name;s=BeautifulSoup(page.read_text(),'html.parser')
 for el in s.select('[href],[src],[poster]'):
  for a in ['href','src','poster']:
   if el.get(a):checkurl(page,el[a])
# Only new Week5 navigation targets in shared pages; do not relabel preexisting links.
for name in ['index.html','labs/learning-path.html','labs/assessments.html']:
 page=COURSE/name;s=BeautifulSoup(page.read_text(),'html.parser')
 for el in s.select('[href]'):
  url=el['href']
  if 'week05' in url or 'postmidterm-05' in url:checkurl(page,url)
record('Week5 local resources and linked chapter anchors resolve',not missing and not badanchors,{'checked_links':len(urlchecks),'missing':missing,'bad_anchors':badanchors,'external_urls':sorted(external)})
form='https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=5'
record('Session5 anonymous form and November dates are explicit',all(form in str(s) and '13 November' in s.get_text() and '6 November' in s.get_text() and 'anonymous' in s.get_text().lower() for s in [player,study]),{'form':form,'independent_lesson_date':'2026-11-06','onsite_return_date':'2026-11-13'})
media=[]
for name in ['week05-lecture.mp4','week05-captions.vtt','week05-poster.png']:
 public=COURSE/'media/week05'/name;original=HOME/'Documents/Projects/Adv thermo/outputs/week05-video'/name
 media.append({'file':name,'sha256':sha(public),'bytes':public.stat().st_size,'matches_final_output':sha(public)==sha(original)})
record('Published media copies match final validated outputs',all(r['matches_final_output'] for r in media) and media[0]['sha256']==timeline['video_sha256'],media)
version=media[0]['sha256'][:12]
record('Video and caption URLs share final hash version',all(urlsplit(el['src']).query=='v='+version for el in player.select('video source[src],video track[src]')),{'version':version})
qa={name:json.loads((SOURCE/'qa'/name).read_text()) for name in ['video-qa.json','audio-audio-qa.json','asr-review.json','controller-qa.json']}
record('Sourcepack carries passing media and controller receipts',all(x.get('passed') for x in qa.values()),{k:{'passed':v.get('passed'),'status':v.get('status'),'reviewed_track_count':v.get('reviewed_track_count')} for k,v in qa.items()})
reviewpath=SOURCE/'media/qa-audio-review-decisions.json'
record('Hash-bound ASR decisions included for reproducibility',reviewpath.exists(),{'required_file':rel(reviewpath)})
cases=[];R=8.31446261815324
for letter,T,P,route in [('a',350,100,'direct'),('b',350,400,'direct'),('c',400,100,'vh')]:
 f=SOURCE/f'media/downloads/week05-case-{letter}.json';d=json.loads(f.read_text());i=d['input'];e=d['equilibrium']
 lnK=4000/(R*350)+50000/R*(1/350-1/T);K=math.exp(lnK);extent=math.sqrt(K/(K+4*P/100));composition=e['composition'];n={x['name']:x['n'] for x in composition};atom=2*n['A2']+n['A'];y={x['name']:x['y'] for x in composition};Q=y['A']**2/y['A2']*P/100
 selected=d['methods'][route]
 savedcontrols=d['workspace']['controls']
 valid= i['T']==T and i['P']==P and i['Pstandard']==100 and i['Tr']==350 and i['Cp']==0 and i['inert']==0 and i['reference']==route and abs(e['xi']-extent)<1e-8 and abs(atom-2)<1e-10 and abs(Q-K)<1e-6 and abs(selected['K']-K)<1e-8 and d['reflection']=='' and savedcontrols['rx-reflection']=='' and float(savedcontrols['rx-T'])==T and float(savedcontrols['rx-P'])==P
 cases.append({'case':letter.upper(),'T_K':T,'P_kPa':P,'route':route,'K':selected['K'],'extent_mol':e['xi'],'atom_balance_mol':atom,'quotient':Q,'valid':valid})
record('Three exported cases reproduce analytic chemistry and clean teaching inputs',all(c['valid'] for c in cases),cases)
# Inspect changed textual course files only. Never print matched credential values.
secret_patterns={
 'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'github_token':re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
 'openai_key':re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b'),
 'aws_key':re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
 'jwt':re.compile(r'\beyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b'),
}
findings=[];textcount=0
privatefiles=[]
for name in changed:
 p=SITE/name
 if not p.is_file():continue
 if p.name.startswith('.env') or p.suffix.lower() in ['.onnx','.wav','.bin','.sqlite','.db'] or re.search(r'(?:responses-redacted|report-snapshot|course_responses|instructor-private)',name):privatefiles.append(name)
 if p.suffix.lower() not in ['.html','.css','.js','.mjs','.py','.json','.qmd','.md','.txt','.vtt','.yml','.yaml']:continue
 try:s=p.read_text()
 except UnicodeDecodeError:continue
 textcount+=1
 for label,pattern in secret_patterns.items():
  if pattern.search(s):findings.append({'file':name,'pattern':label,'value':'REDACTED'})
 if re.search(r'"(?:submission_key|student_id|studentId|response_id)"\s*:\s*"[^"\s]{5,}"',s):findings.append({'file':name,'pattern':'private_response_identifier','value':'REDACTED'})
record('No private records, model weights, raw audio or credential-like material in changed files',not findings and not privatefiles,{'text_files_screened':textcount,'findings':findings,'excluded_artifacts_found':privatefiles,'scope':'Changed files under course2105603 only. Pattern screen, not a formal secret-security guarantee.'})
record('No stale draft timing metadata in player',all(c['start']>=0 and c['end']>c['start'] for c in chapters) and all(abs(a['end']-b['start'])<1e-9 for a,b in zip(chapters,chapters[1:])),{'contiguous':True})
report={'audited_at_utc':datetime.now(timezone.utc).isoformat(),'actor':'Codex /root/week05_narration','mode':'read-only release audit; only this local receipt is written','site':'~/.codex/worktrees/week05-video/Test','git_head_at_audit':git('rev-parse','HEAD').strip(),'working_tree_snapshot':'Release edits in progress; no assertion of clean Git state or live deployment.','passed':not issues,'failed_checks':issues,'checks':checks,'files_changed_at_start':changed,'limitations':['Live HTTP deployment and browser playback are verified separately by root.','Offline bundle/manifest updates may be finishing concurrently.','Full subjective listening review was not performed.']}
OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'checks':len(checks),'failed_checks':issues,'output':str(OUTPUT)},indent=2))
