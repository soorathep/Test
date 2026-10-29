"""Prepare matching core HTML/QMD copies without touching the canonical site.

Only setup and the current-route/optional-H sections change. The 40 slide IDs,
scientific case text, QR code and other content remain intact.
"""
from pathlib import Path
import json,re
P=Path(__file__).parent
SITE=Path.home()/'Documents/GitHub/Test'
source_qmd=SITE/'_teaching-src/2105603/postmidterm-04.qmd'
source_html=SITE/'teaching/2105603/postmidterm-04.html'
qmd=source_qmd.read_text();html=source_html.read_text()
original_qmd=qmd;original_html=html

def replace_section(text,ident,func,is_html):
    pattern=(r'<section id="'+re.escape(ident)+r'"[^>]*>.*?</section>' if is_html
             else r'^## [^\n]*\{#'+re.escape(ident)+r'(?:\s[^}]*)?\}.*?(?=^## |\Z)')
    matches=list(re.finditer(pattern,text,re.S|re.M))
    assert len(matches)==1,(ident,len(matches))
    match=matches[0];new=func(match[0])
    assert new!=match[0],ident
    return text[:match.start()]+new+text[match.end():]

def setup_q(s):
    s=s.replace('**Your action:** Open the worksheet and Lab guide. Keep your first answers, then add corrections after each check.',
                '**Your action:** Complete the [video opening](week04-video.html#opening-01) and R1–R3 first, or use the [written alternative](week04-questions.html). Then open the worksheet and Lab guide. Keep attempts and corrections.')
    s=s.replace('Sections A–I.','A–G and I required; H1–H4 optional.')
    s=s.replace('[Printable slides](files/postmidterm-04-slides.pdf)','[Complete video slides](files/week04-video-slides.pdf) · [Core slide reference](files/postmidterm-04-slides.pdf)')
    return s

def setup_h(s):
    s=s.replace('<strong>Your action:</strong> Open the worksheet and Lab guide. Keep your first answers, then add corrections after each check.',
                '<strong>Your action:</strong> Complete the <a href="week04-video.html#opening-01">video opening</a> and R1–R3 first, or use the <a href="week04-questions.html">written alternative</a>. Then open the worksheet and Lab guide. Keep attempts and corrections.')
    s=s.replace('Sections A–I.','A–G and I required; H1–H4 optional.')
    s=s.replace('<a href="files/postmidterm-04-slides.pdf">Printable slides</a>','<a href="files/week04-video-slides.pdf">Complete video slides</a> · <a href="files/postmidterm-04-slides.pdf">Core slide reference</a>')
    return s

route_q='''## The study route {#the-study-route}

::: {.your-action}
**Your action:** Keep R1–R3 with your worksheet. Record your actual study time. Do not repeat the written opening after watching it.
:::

- **Opening:** watch once and write R1–R3 during its four-minute pause.
- **A–D:** processes, solubility, inventory and Lab 10.
- **Break:** take 10 minutes away from the screen.
- **E–G:** adsorption, vessel balance and Lab 11.
- **I:** submit the exit ticket and feedback once.

Core work totals **100 minutes**. Together with the **four-minute R1–R3 pause**, required work totals **104 minutes**, plus the **10-minute break** and combined recording. The video page reports measured recording and planned total times, approximately three hours overall.

**H1–H4 is optional** and adds about **20 minutes** if you choose it. These allocations are study activities, not video timestamps.

'''
route_h='''<section id="the-study-route" class="slide level2">
<h2>The study route</h2>
<div class="your-action"><p><strong>Your action:</strong> Keep R1–R3 with your worksheet. Record your actual study time. Do not repeat the written opening after watching it.</p></div>
<ul>
<li><strong>Opening:</strong> watch once and write R1–R3 during its four-minute pause.</li>
<li><strong>A–D:</strong> processes, solubility, inventory and Lab 10.</li>
<li><strong>Break:</strong> take 10 minutes away from the screen.</li>
<li><strong>E–G:</strong> adsorption, vessel balance and Lab 11.</li>
<li><strong>I:</strong> submit the exit ticket and feedback once.</li>
</ul>
<p>Core work totals <strong>100 minutes</strong>. Together with the <strong>four-minute R1–R3 pause</strong>, required work totals <strong>104 minutes</strong>, plus the <strong>10-minute break</strong> and combined recording. The video page reports measured recording and planned total times, approximately three hours overall.</p>
<p><strong>H1–H4 is optional</strong> and adds about <strong>20 minutes</strong> if you choose it. These allocations are study activities, not video timestamps.</p>
</section>'''

def brief_q(s):
    return s.replace('## Unseen case brief','## Optional unseen-case practice').replace(
        '**Your action:** Read **H1–H4, worksheet p. 6**. Use the equations from slides 11, 22 and 27. Keep the worked solutions closed.',
        '**Your action:** For the required route, go to [exit ticket and feedback](#/exit-ticket). Optional H1–H4 on worksheet p. 6 adds practice; attempt it before opening the solutions. Use slides 11, 22 and 27.')

def brief_h(s):
    return s.replace('<h2>Unseen case brief</h2>','<h2>Optional unseen-case practice</h2>').replace(
        '<strong>Your action:</strong> Read <strong>H1–H4, worksheet p.&nbsp;6</strong>. Use the equations from slides 11, 22 and 27. Keep the worked solutions closed.',
        '<strong>Your action:</strong> For the required route, go to <a href="#/exit-ticket">exit ticket and feedback</a>. Optional H1–H4 on worksheet p. 6 adds practice; attempt it before opening the solutions. Use slides 11, 22 and 27.')

def attempt_q(s):
    return s.replace('## Unseen attempt {#unseen-attempt .work-stop}','## Choose whether to attempt H {#unseen-attempt}').replace(
        '**Your action:** Pause for about **20 minutes**. Complete **H1–H4, worksheet p. 6**, before viewing slide 37.',
        '**Your action:** Choose your route. Continue to [exit ticket and feedback](#/exit-ticket) to finish the required lesson. If you choose optional **H1–H4, worksheet p. 6**, allow about **20 extra minutes** and attempt it before slide 37. No mandatory H pause is required.')

def attempt_h(s):
    return s.replace('class="slide level2 work-stop"','class="slide level2"').replace('<h2>Unseen attempt</h2>','<h2>Choose whether to attempt H</h2>').replace(
        '<strong>Your action:</strong> Pause for about <strong>20 minutes</strong>. Complete <strong>H1–H4, worksheet p.&nbsp;6</strong>, before viewing slide 37.',
        '<strong>Your action:</strong> Choose your route. Continue to <a href="#/exit-ticket">exit ticket and feedback</a> to finish the required lesson. If you choose optional <strong>H1–H4, worksheet p. 6</strong>, allow about <strong>20 extra minutes</strong> and attempt it before slide 37. No mandatory H pause is required.')

transforms={'your-independent-lesson':(setup_q,setup_h),'the-study-route':(lambda _:route_q,lambda _:route_h),'unseen-case-brief':(brief_q,brief_h),'unseen-attempt':(attempt_q,attempt_h)}
for ident,(q,h) in transforms.items():
    qmd=replace_section(qmd,ident,q,False)
    html=replace_section(html,ident,h,True)

ids=lambda t:re.findall(r'<section id="([^"]+)"',t)
assert ids(html)==ids(original_html) and len(ids(html))==40
for ident in ids(original_html):
    if ident in transforms:continue
    pattern=r'<section id="'+re.escape(ident)+r'"[^>]*>.*?</section>'
    assert re.search(pattern,html,re.S)[0]==re.search(pattern,original_html,re.S)[0],ident
assert '120 minutes of work' not in qmd and '120 minutes of work' not in html
(P/'postmidterm-04.qmd').write_text(qmd)
(P/'postmidterm-04.html').write_text(html)
(P/'core-slide-sync-qa.json').write_text(json.dumps({'status':'passed','slide_count':40,'ids_and_order_preserved':True,'changed_sections':list(transforms),'other_sections_byte_identical':True,'canonical_writes':False},indent=2)+'\n')
print('Prepared 40-slide core HTML and QMD copies; four setup/route sections revised; all other HTML sections byte-identical.')
