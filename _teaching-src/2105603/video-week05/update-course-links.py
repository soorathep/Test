"""Update the Week 5 route in a selected local website checkout."""
from pathlib import Path
import argparse
import json
import re

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--site',type=Path,required=True)
    a=parser.parse_args(); p=a.site/'teaching/2105603'
    form='https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=5'
    route='''<section class="learning-session" id="session-5">
<p class="eyebrow mono">Week 5 · Independent lesson · Friday 6 November 2026</p>
<h2>Chemical equilibrium and routes to K</h2>
<p><strong>No in-person class on 6 November.</strong> Follow the video, worksheet and Lab 12 at your own pace within the planned approximately three-hour lesson. We return <strong>onsite on Friday 13 November</strong>; bring your unresolved questions.</p>
<p><a href="../week05-study.html"><strong>Start here: instructions and activity schedule</strong></a> · <a href="../week05-video.html">Narrated video and Lab 12 demonstrations</a> · <a href="../files/week05-practice.pdf">Worksheet · 6 pages</a></p>
<p><strong>Main question:</strong> Why can equilibrium composition change while K stays the same?</p>
<p>Start with the brief answers to Week 4 questions about partial pressure, adsorption and independent balance checks. Then use one synthetic A2 ⇌ 2A example to calculate K from Gibbs energy and enthalpy/entropy, solve for extent, and compare pressure and temperature changes.</p>
<p><strong>Required Lab:</strong> <a href="reaction.html#rx-experiment">Lab 12 · Chemical equilibrium</a>. Use the <a href="../files/week05-lab-guide.pdf">two-page control guide</a> when instructed. Attempt each worksheet question before the <a href="../files/week05-solutions.pdf">worked solutions</a>. The real-interface demonstrations are in video chapters 20, 22 and 30.</p>
<p><a href="../postmidterm-05.html">Lesson slides · 32 slides</a> · <a href="../files/postmidterm-05-slides.pdf">Slide PDF</a> · <a href="../files/preclass-week-05.pdf">Optional background reading</a> · <a href="../postmidterm-05-appendix.html">Optional appendix</a></p>
<p><strong>One required worksheet:</strong> complete R, A-F and G within the lesson. Record the 350 K/100 kPa baseline, 350 K/400 kPa pressure case and 400 K/100 kPa constant-enthalpy case. Set ΔCp°=0 and select the named K source. Check atom conservation and Q=K independently, save the three calculator exports and restore one. No extra preparation or follow-up assignment is required.</p>
<p>Use the pause budgets as a guide. If a step remains unresolved at the end of its budget, record the sticking point and continue. The video page reports the measured recording duration plus the 128-minute work budget and 10-minute break. Report your actual study time, not the planned total.</p>
<p><strong>Final 10-minute checkpoint:</strong> <a href="FORM">Session 5 exit ticket and feedback</a>. Include numerical evidence and an unresolved question if needed. Submit once and wait for “Response received.” This anonymous form does not identify individual attendance.</p>
<p><a href="assessments.html#session-5">Week 5 evidence checklist</a>. Keep your worksheet, first attempts, corrections and exported cases for the onsite discussion.</p>
</section>'''.replace('FORM',form)
    pattern=re.compile(r'<section\b[^>]*\bid=["\']session-5["\'][^>]*>.*?</section>',re.S)
    f=p/'labs/learning-path.html';s=f.read_text()
    assert len(pattern.findall(s))==1;s=pattern.sub(lambda _:route,s)
    replacements={
      'Sessions 1, 5 and 6 use 12-slide classroom decks and 70 minutes of pair work. Sessions 2–4 are independent lessons with their own approximately three-hour schedules.':'Sessions 1 and 6 use classroom teaching. Sessions 2–5 are independent lessons with narrated videos, calculations and Lab practice. Week 5 replaces the class on 6 November; onsite teaching resumes on 13 November.',
      'Standard classroom sessions: 1, 5 and 6':'Standard classroom sessions: 1 and 6',
      'For Sessions 1, 5 and 6,':'For Sessions 1 and 6,',
      'Sessions 2–4 instead follow':'Sessions 2–5 instead follow',
      'Session 2, Session 3 and Session 4 narrated videos':'Session 2, Session 3, Session 4 and Session 5 narrated videos',
      'including the Session 3 and Session 4 worksheets, worked solutions and Lab guides':'including the Session 3, Session 4 and Session 5 worksheets, worked solutions and Lab guides',
    }
    for before,after in replacements.items():s=s.replace(before,after)
    marker='<h2>Electrochemical equilibrium</h2>'
    notice='<p><strong>Onsite class: Friday 13 November 2026.</strong> Bring remaining questions from the independent video lessons.</p>'
    if notice not in s:s=s.replace(marker,marker+notice,1)
    f.write_text(s)
    f=p/'labs/assessments.html';s=f.read_text();assert len(pattern.findall(s))==1
    assessment=route.replace('<h2>Chemical equilibrium and routes to K</h2>','<h2>5. Chemical equilibrium and routes to K</h2>').replace('<p><a href="assessments.html#session-5">Week 5 evidence checklist</a>. Keep your worksheet, first attempts, corrections and exported cases for the onsite discussion.</p>','<p><strong>Evidence checklist:</strong> retain the reaction basis and standard-state convention; calculations of K and extent; three controlled cases; independent atom and Q checks; one verified JSON restore; corrections and model limits.</p>')
    f.write_text(pattern.sub(lambda _:assessment,s))
    f=p/'index.html';s=f.read_text()
    s=s.replace('Sessions 1, 5 and 6 are classroom sessions. Sessions 2–4 are independent lessons','Sessions 1 and 6 are classroom sessions. Sessions 2–5 are independent lessons')
    s=s.replace('Sessions 1, 5 and 6 use classroom teaching slides; Sessions 2–4 use independent study routes','Sessions 1 and 6 use classroom teaching slides; Sessions 2–5 use independent study routes')
    start=s.index('<li style="margin-bottom:12px"><strong>Session 5:')
    end=s.index('</li>',start)+5
    base='{{ site.baseurl }}/teaching/2105603/'
    s=s[:start]+f'''<li style="margin-bottom:12px"><strong>Session 5: Chemical equilibrium and routes to K · Independent lesson, 6 November</strong><br><a href="{base}week05-study.html"><strong>Start the independent lesson</strong></a> · <a href="{base}week05-video.html"><strong>Watch the video and Lab 12 demonstrations</strong></a> · <a href="{base}postmidterm-05.html">Lesson slides</a> · <a href="{base}files/postmidterm-05-slides.pdf">Slide PDF</a> · <a href="{base}files/week05-practice.pdf">Worksheet (6 pages)</a> · <a href="{base}files/week05-lab-guide.pdf">Lab guide</a> · <a href="{base}files/week05-solutions.pdf">Worked solutions</a> · <a href="{form}">Exit ticket and feedback</a><br><small>No in-person class on 6 November. Follow the video and activities for approximately three hours. Onsite teaching resumes Friday 13 November.</small></li>'''+s[end:]
    s=s.replace('<strong>Session 6: Electrochemical equilibrium</strong>','<strong>Session 6: Electrochemical equilibrium · Onsite, 13 November</strong>')
    f.write_text(s)
    f=p/'labs/assets/learning-path.json';d=json.loads(f.read_text());week=next(x for x in d['sessions'] if x['number']==5)
    week.update(delivery='independent',date='2026-11-06',nextOnsiteDate='2026-11-13',video='week05-video.html',studyHub='week05-study.html',worksheet='files/week05-practice.pdf',worksheetPages=6,labGuide='files/week05-lab-guide.pdf',solutions='files/week05-solutions.pdf',prereadingOptional=True,exitWindow='final 10 minutes',preparation='No required preparation. Keep the six-page worksheet beside the video.',deliverable='One worksheet, three Lab 12 cases, independent atom and Q checks, and one JSON restore within the lesson.',optionalPractice='Optional: examine nonzero heat capacity, reverse the reaction or scale all coefficients and properties consistently.')
    f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    f=p/'labs/assets/learning-guide.js';s=f.read_text();s=s.replace("independent?`Study minutes ${session.exitWindow||'172–180'}: exit ticket + feedback`", "independent?(session.number===5?'Final 10 minutes: exit ticket + feedback':`Study minutes ${session.exitWindow||'172–180'}: exit ticket + feedback`)")
    f.write_text(s)
    print('Updated Week 5 navigation and the 13 November onsite notice.')

if __name__=='__main__':main()
