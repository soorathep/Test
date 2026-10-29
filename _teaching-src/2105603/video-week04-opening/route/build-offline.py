"""Build a student-only portable website with the Week 4 questions-first route.

Reviewed snapshot of the existing Labs offline builder. Set SKH_WEBSITE_DIR to
the website checkout. Large media and their players remain online; links retain
chapter fragments. Run only after the reviewed Week 4 question page, hub,
player, worksheet and navigation changes have been staged. The opening page
is included by the existing course-HTML copy rule; no new data allowlist is added.
"""
import os
from pathlib import Path
import hashlib, json, re, shutil, tempfile, zipfile
site=Path(os.environ.get('SKH_WEBSITE_DIR',str(Path.home()/'Documents/GitHub/Test')))
course=site/'teaching/2105603'
output=course/'files/thermodynamics-offline.zip'
with tempfile.TemporaryDirectory(prefix='thermo-offline-') as temp:
    root=Path(temp)/'thermodynamics-offline'; dest=root/'teaching/2105603'; dest.mkdir(parents=True)
    for directory in ('labs','site_libs','figures','assets','images'):
        shutil.copytree(course/directory,dest/directory,ignore=shutil.ignore_patterns('*.mp4','*.m4a','*.wav'))
    for file in course.glob('*.html'):
        if file.name not in ('index.html','week02-video.html','week03-video.html','week04-video.html','lab08-video.html','lab01-video.html','week03-gibbs-review-video.html'): shutil.copy2(file,dest/file.name)
    (dest/'files').mkdir()
    for file in (course/'files').iterdir():
        if file.suffix in ('.pdf','.ipynb') and file.name not in {n+'-slides.pdf' for n in ('eos','fugacity','solution','vle','stability','reaction')}: shutil.copy2(file,dest/'files'/file.name)
    # The PDF glob above includes the complete opening + core video slides.
    assert (dest/"files/week04-video-slides.pdf").is_file(), 'Stage the complete Week 4 video slide PDF before building the offline ZIP.'
    # Explicitly allow only the synthetic Lab 08 demonstration files.
    for name in ('lab08-demo.xlsx', 'lab08-demo-K-kPa.csv', 'lab08-demo-excel-export.csv', 'lab08-baseline.json', 'lab08-margules-study.json', 'lab08-nrtl-study.json', 'lab08-margules-residuals.csv', 'lab08-nrtl-residuals.csv', 'lab08-restored-nrtl.jpg'):
        shutil.copy2(course/'files'/name,dest/'files'/name)
    # The Lab 01 synthetic comparison is generated from the recorded demonstration.
    lab01_comparison=course/'files/lab01-demo-comparison.json'
    if lab01_comparison.exists(): shutil.copy2(lab01_comparison,dest/'files'/lab01_comparison.name)
    # This reviewed Lab 04 export is synthetic demonstration evidence, not a student submission.
    review_json=course/'files/gibbs-review-lab04-study.json'
    if review_json.exists(): shutil.copy2(review_json,dest/'files'/review_json.name)
    # No nested archives, private source, credentials or private instructor keys.
    # Student worked solutions are intentionally available after an attempted worksheet.
    if (site/'favicon.png').exists(): shutil.copy2(site/'favicon.png',root/'favicon.png')
    home='<!doctype html><html lang="en"><meta charset="utf-8"><title>Thermodynamics offline</title><h1>Advanced thermodynamics</h1><p><a href="/teaching/2105603/labs/learning-path.html">Six-session learning path</a></p><p><a href="/teaching/2105603/labs/assessments.html">Assessment sets</a></p><p>External references require internet. Labs and included slides run locally. The six pre-class PDFs are linked from the learning path.</p><p>Session 2 video and narration are not included in this ZIP. <a href="https://www.skhgroup.net/teaching/2105603/week02-video.html">Open the online lesson</a> with internet access, or use its separately downloaded MP4 videos. The slides, worksheet and Labs are included here.</p><p>The <a href="https://www.skhgroup.net/teaching/2105603/lab08-video.html">Lab 08 video walkthrough</a> also requires internet or its separate MP4 download. The Excel workbook, CSV examples and written guide are included locally.</p><p><a href="/teaching/2105603/week03-study.html">Session 3 independent study guide</a>: consistency tests before liquid stability and LLE. The slides, six-page worksheet, four-page worked solutions, four-page Lab guide and optional background PDF are included locally. Follow the same 180-minute route with the included slides and documents. The <a href="https://www.skhgroup.net/teaching/2105603/week03-video.html">Week 3 narrated video</a> is online or a separate MP4 download. The final anonymous exit ticket and feedback require internet.</p><p><a href="https://www.skhgroup.net/teaching/2105603/week04-video.html#opening-01">The Week 4 video now includes the questions-first opening</a>, with a four-minute R1-R3 pause before the core lesson. Use the <a href="/teaching/2105603/week04-questions.html">written opening</a> as the offline alternative, then continue to the core slides. Do not add both reading and watching as separate required activities. The <a href="/teaching/2105603/week04-study.html">ECS replacement lesson route</a> gives the measured video duration and planning total. The opening, slides, six-page worksheet, four-page guide, four-page worked solutions and optional background are included locally. A-G and I, Lab 10 and Lab 11 remain required; H1-H4 is optional. For the video route, add four minutes for R1-R3, 100 minutes for core work and a 10-minute break to the combined recording. The MP4 and player are online or a separate download. Submit the existing Session 4 exit ticket and feedback once; no extra form is added.</p></html>'
    home=home.replace('</html>','<p>The supplemental <a href="https://www.skhgroup.net/teaching/2105603/lab01-video.html">Week 1 Lab 01 video walkthrough</a> is online or a separate MP4 download. Its <a href="/teaching/2105603/files/week01-lab-guide.pdf">four-page guide</a> is included. This revisits the completed classroom lesson and needs no repeat form submission.</p></html>')
    home=home.replace('</html>','<p>Optional Gibbs and stability review: the <a href="/teaching/2105603/week03-gibbs-review.html">26-slide review</a>, <a href="/teaching/2105603/files/week03-gibbs-review-guide.pdf">four-page guide</a> and <a href="/teaching/2105603/files/gibbs-review-lab04-study.json">synthetic Lab 04 study JSON</a> are included. The <a href="https://www.skhgroup.net/teaching/2105603/week03-gibbs-review-video.html">narrated review with actual Lab 04 demonstrations</a> is online or a separate MP4 download. It adds no attendance or repeat exit-ticket submission.</p></html>')
    (root/'index.html').write_text(home);(dest/'index.html').write_text(home)
    for file in root.rglob('*.html'):
        s=file.read_text()
        s=re.sub(r'<link\b[^>]*href=["\']https://fonts\.(?:googleapis|gstatic)\.com[^>]*>','',s)
        s=s.replace('../files/thermodynamics-offline.zip','/README.txt')
        # The course media/ directory is not copied; link to the online players.
        for video_page in ('week02-video.html','week03-video.html','week04-video.html','lab08-video.html','lab01-video.html','week03-gibbs-review-video.html'):
            # Preserve chapter fragments and query strings when the player is omitted.
            pattern = r'href=(["\'])(?:\.\./|\./|/teaching/2105603/)?' + re.escape(video_page) + r'([?#][^"\']*)?\1'
            s = re.sub(pattern, lambda m: 'href=' + m[1] +
                       'https://www.skhgroup.net/teaching/2105603/' + video_page +
                       (m[2] or '') + m[1], s)
        for name in ('eos','fugacity','solution','vle','stability','reaction'):
            s=s.replace('files/'+name+'-slides.pdf',name+'.html')
        # Toolkits are optional source archives, not needed for the interactive labs.
        s=re.sub(r'href="(?:\./)?files/[^"\n]+\.zip"','href="/README.txt"',s)
        file.write_text(s)
    # The dynamic learning panel reads this JSON after page load, so its video
    # targets must also point online when MP4 players are omitted from the ZIP.
    learning_data=dest/'labs/assets/learning-path.json'
    learning=json.loads(learning_data.read_text())
    for session in learning['sessions']:
        if session.get('video'):
            session['video']='https://www.skhgroup.net/teaching/2105603/'+session['video']
        if session.get('supplementalVideo'):
            session['supplementalVideo']='https://www.skhgroup.net/teaching/2105603/'+session['supplementalVideo']
    learning_data.write_text(json.dumps(learning,ensure_ascii=False,indent=2)+'\n')
    (root/'serve.py').write_text('''"""Serve this extracted directory on loopback only, using Python standard library."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import webbrowser
root=Path(__file__).resolve().parent
with ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(root))) as server:
    url=f"http://127.0.0.1:{server.server_port}/"
    print("Open",url,"; press Ctrl+C to stop",flush=True)
    webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
''')
    (root/'README.txt').write_text('''2105603 ADVANCED THERMODYNAMICS: OFFLINE STUDENT PACKAGE

Extract the ZIP before use. Requires a browser and an installed Python 3.
Run serve.py with the ABSOLUTE PATH to your Python interpreter, for example:
  ~/.venvs/research/bin/python /absolute/path/thermodynamics-offline/serve.py
Use your own installed interpreter path on Windows or Linux.
The server uses only the standard library and listens on 127.0.0.1.
It prints a local URL and opens your browser. Ctrl+C stops the server.
Opening HTML through file:// will not reliably run data fetches or workers.

Includes all 13 labs, six session slides, reference decks, assessment sets,
six session PDFs, six pre-class reading PDFs and available notebooks. Reference decks use HTML to avoid
duplicating their large figures in PDFs. No private instructor key or student records.
Student-facing worked solutions are included; attempt the worksheet first.
External literature and other group website pages need internet.
The supplemental Week 1 Lab 01 walkthrough is available online or as a separate
MP4 download: https://www.skhgroup.net/teaching/2105603/lab01-video.html
Its four-page guide is included. No repeat form submission is required.
Session 2 video and narration are not included in this ZIP. Use the online
lesson with internet access or its separately downloaded MP4 videos:
https://www.skhgroup.net/teaching/2105603/week02-video.html
The Session 2 slides, four-page worksheet and Labs are included locally.
Session 3 is an independent holiday lesson: consistency tests
before liquid stability and LLE. Its study guide, slides, six-page worksheet,
four-page worked solutions, four-page Lab guide and optional background PDF are
included locally. Plan approximately180 minutes for the recording or slides,
independent work, review and a break; actual completion time varies.
Open teaching/2105603/week03-study.html through the local server to begin.
The Session 3 narrated video is online or a separate MP4 download:
https://www.skhgroup.net/teaching/2105603/week03-video.html
The optional Gibbs and stability review slides, slide PDF, four-page guide
and synthetic Lab 04 demonstration study JSON are included. The review video
requires internet or a separate MP4 download:
https://www.skhgroup.net/teaching/2105603/week03-gibbs-review-video.html
The demonstration JSON is synthetic evidence, not a student submission. Restore
it and recompute in Lab 04. This review adds no attendance or repeat exit ticket.
The offline slide/document route covers the same activities; video is not
additional required study. Downloaded MP4s require manual activity pauses.
Session 4 replaces class while the instructor attends the ECS meeting.
The Week 4 combined video begins with Opening 01-14 and includes a four-minute
R1-R3 notebook pause before the core lesson. For offline study, use
teaching/2105603/week04-questions.html as the alternative written opening,
then follow the core slides. Do not add both as separate required activities.
The opening, complete video slide PDF, 40-slide core deck, six-page worksheet, four-page Lab guide,
four-page worked solutions and optional background reading are included.
A-G and I, Lab 10 and Lab 11 remain required; H1-H4 is optional.
For the video route, add 4 minutes for R1-R3, 100 minutes for core work and
10 minutes for the break to the combined recording. Read the staged study
hub for its measured duration and conservative planning total.
Video links preserve the new #opening-01 and existing #slide-16/#slide-30
chapter anchors. The recording and player remain online or a separate download:
https://www.skhgroup.net/teaching/2105603/week04-video.html
Its chapter links preserve the Lab 10 / Lab 11 demonstration anchors.
Complete the existing Session 4 exit ticket and feedback once, with internet.
There is no additional form and no repeat Week 3 submission.
The Lab 08 demonstration includes its synthetic Excel workbook, CSV, saved
study examples, residual tables and the English walkthrough page.
The Lab 08 video and audio are not included. Open the narrated walkthrough
with internet access or download its MP4 separately:
https://www.skhgroup.net/teaching/2105603/lab08-video.html
The exit ticket and feedback form also require internet to submit responses.
The offline archive does not store or synchronize student responses.
Optional source toolkit ZIPs are omitted; their links lead to this note.
Python notebooks and figure regeneration need their documented dependencies;
they are not required to run the browser labs. No packages are installed here.
Imported student data stay in the browser unless you export them. Keep your
exported study JSON and worksheet together. New study exports restore inputs;
recalculate after restore. Offline data are not synchronized to the live site.

MANIFEST.json records file hashes for this build. Lab release metadata is in
teaching/2105603/labs/release-manifest.json. Third-party assets retain their
bundled license headers; course assets retain their existing attribution.
''')
    manifest={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(root.rglob('*')) if f.is_file()}
    (root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for file in sorted(root.rglob('*')):
            if file.is_file(): z.write(file,str(file.relative_to(root.parent)))
    if output.stat().st_size>=100_000_000: raise RuntimeError('Archive exceeds safe repository file size')
    print(f'{output}: {output.stat().st_size/1e6:.1f} MB; {len(manifest)} files')
