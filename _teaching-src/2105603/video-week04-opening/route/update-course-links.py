"""Update only Session 4 in course navigation HTML and its JSON metadata.

Run after staging the reviewed week04-study.html in the selected website tree.
The new schedule is copied from that page. Other weeks and surrounding bytes
are preserved. This script does not touch Labs code or release metadata.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re


SECTION = re.compile(r'<section\b[^>]*\bid=["\']session-4["\'][^>]*>.*?</section>', re.S)
FORM = 'https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=4'

PLANNING = None  # Populated from the measured timing in the staged lesson hub.
CORE = (
    'Watch Opening 01-14 at the start of the integrated video. Pause for four '
    'minutes at Opening 13 to write R1-R3 in your notebook; check at Opening 14. '
    'The written opening is an alternative or reference, not another required activity. '
    'Then complete A1-A3 and B1-B2 on worksheet p. 1; C1-C3 on p. 2; D1-D4 '
    'on p. 3 using Lab 10; E1-E3 and F1-F3 on p. 4; G1-G4 on p. 5 using Lab 11; '
    'and I on p. 6. Write predictions before the demonstrations on slides 16 '
    'and 30. Independently rerun the three prescribed cases in each Lab, '
    'calculate balances and reopen a saved study. H1-H4 on p. 6 is optional; '
    'use the player link to skip optional slides 35-38 and continue to slide 39. '
    'The opening replaces the former required H work.'
)
COMPLETION = (
    'At the final 10-minute checkpoint, complete the existing Session 4 exit '
    'ticket and feedback: explain finite-inventory GSE, include Lab 10 and '
    'Lab 11 numerical evidence, and report actual study minutes and pacing. '
    'Submit once at slide 39, wait for the receipt and verify it at slide 40. '
    'Keep R1-R3 with your worksheet. There is no repeat Week 3 submission or '
    'additional form. The anonymous form does not identify attendance.'
)
OPTIONAL = (
    'H1-H4 on worksheet p. 6 is optional transfer practice; allow about 20 '
    'additional minutes if you choose it, attempt it before the solutions and '
    'keep corrections. Further optional extensions include a binary '
    'SLE/eutectic comparison in Lab 10, Freundlich/BET model windows, '
    'adsorption-data fitting or isosteric heat in Lab 11. Paper exercises on '
    'Henry gas solubility and dilute-solution osmosis remain in the appendix.'
)
EVIDENCE = (
    'Retain R1-R3, process and pressure predictions, solubility and inventory '
    'calculations, three controlled cases from each Lab, one annotated plot '
    'per Lab, explicit gas-plus-solid and gas-plus-adsorbed balances, '
    'reproducible JSON files and model limitations. Distinguish partial from '
    'total pressure and uptake per kg from adsorbed moles. H1-H4 and its '
    'corrections are retained only if you choose the optional extension.'
)
CHECKPOINT = (
    'C uses T=300 K, V=2 L, Psub=8 kPa, volatile inventories 0.010/0.004 mol '
    'and 0.001 mol inert. This is different from the Lab 10 demonstration. '
    'F follows a known-pressure adsorption balance at P=10 kPa, whose required '
    'inventory is different from the 0.010 mol used in Lab 11. Show '
    'substitutions and units before viewing the solutions. Optional H '
    'transfers this reasoning to new GSE conditions and a known-pressure '
    'Langmuir case.'
)


def course_schedule(site: Path) -> str:
    text = (site / 'teaching/2105603/week04-study.html').read_text()
    for required in ('week04-questions.html', '100 minutes', 'Opening 13',
                     'H1-H4', 'optional'):
        if required not in text:
            raise ValueError(f'Stage the reviewed Week 4 hub first; missing {required!r}')
    matches = list(re.finditer(
        r'<table\b[^>]*class=["\'][^"\']*\bstudy-schedule\b[^"\']*["\'][^>]*>.*?</table>',
        text, re.S))
    if len(matches) != 1:
        raise ValueError('Expected exactly one reviewed study schedule table')
    table = matches[0][0].replace('study-schedule', 'learning-path-table')

    def parent_link(match: re.Match) -> str:
        quote, href = match.group(1), match.group(2)
        if not href.startswith(('http:', 'https:', '/', '#', 'mailto:')):
            href = '../' + href
        return f'href={quote}{href}{quote}'

    return re.sub(r'href=(["\'])(.*?)\1', parent_link, table)


def section_learning(table: str) -> str:
    return f'''<section class="learning-session" id="session-4">
<p class="eyebrow mono">Session 4 · Approximately three hours</p>
<h2>Solid equilibria and adsorption</h2>
<p><strong>Main question:</strong> How do phase presence, surface uptake and vessel constraints determine equilibrium pressure?</p>
<p><strong>Start here:</strong> <a href="../week04-video.html#opening-01">Watch the integrated Week 4 video from the beginning</a>. The opening answers your Week 3 questions. Pause for four minutes at Opening 13 for R1-R3, then continue to the main lesson. The <a href="../week04-questions.html">written opening</a> is an alternative or reference, not extra required reading. Keep the <a href="../files/week04-practice.pdf">six-page worksheet</a> beside the video. A-G and I are required; H1-H4 is optional.</p>
<p><a href="../week04-study.html">Study guide and full schedule</a></p>
<p>Open the <a href="../files/week04-lab-guide.pdf">Lab 10 and Lab 11 guide</a> only when a step names its pages. Use the <a href="../files/week04-solutions.pdf">worked solutions</a> after your attempt.</p>
<p><strong>Independent lesson:</strong> This replaces class while the instructor attends the ECS meeting. Video and slides present the same main lesson. <a href="../files/preclass-week-04.pdf">Background reading</a> is optional; no prior compulsory reading is needed.</p>
<p><strong>Planning guide:</strong> {PLANNING}</p>
<h3>Your nominal study route</h3>
<div class="table-scroll" style="max-height:none">{table}</div>
<p><strong>Final checkpoint:</strong> <a href="{FORM}">Session 4 exit ticket and feedback · 10 minutes</a>. Answer individually and wait for the receipt. Internet is required. No name, ID or email is requested.</p>
<p><strong>Outcome:</strong> Interpret consistency and stability evidence, then distinguish pure-solid solubility, finite-inventory sublimation and surface adsorption; independently close gas-solid and gas-adsorbed inventory balances.</p>
<p><a href="../files/week04-video-slides.pdf">Complete video slides (opening + core)</a> · <a href="../postmidterm-04.html">Core slides · reference, 40 pages</a> · <a href="../files/postmidterm-04-slides.pdf">Core slide PDF · reference</a> · <a href="../stability.html">Module reference deck</a> · <a href="../postmidterm-04-appendix.html">Optional session appendix</a></p>
<p><strong>Required labs:</strong> <a href="solids.html#so-experiment">10 · SLE and gas-solid equilibrium</a> · <a href="adsorption.html#ad-experiment">11 · Adsorption</a></p>
<p><a href="assessments.html#session-4">Lesson tasks and evidence checklist</a></p>
<p><strong>Work within the planned lesson:</strong> {CORE}</p>
<p><strong>Optional practice:</strong> {OPTIONAL}</p>
<p><strong>Complete and retain:</strong> {COMPLETION}</p>
</section>'''


def section_assessments() -> str:
    return f'''<section class="learning-session" id="session-4">
<h2>4. Solids and adsorption</h2>
<p><a href="../week04-video.html#opening-01">Integrated Week 4 video · opening and main lesson</a> · <a href="../week04-questions.html">Written opening · alternative or reference</a> · <a href="../files/week04-practice.pdf">Six-page worksheet · A-G and I required, H optional</a></p>
<p><a href="../week04-study.html">Study guide and full schedule</a> · <a href="learning-path.html#session-4">Session resources</a></p>
<p>Open the <a href="../files/week04-lab-guide.pdf">Lab 10 and Lab 11 guide</a> at the named steps. Open the <a href="../files/week04-solutions.pdf">worked solutions</a> after attempting each task. <a href="../files/preclass-week-04.pdf">Background reading</a> is optional.</p>
<h3>Required activities within the planned lesson</h3>
<p>{CORE}</p>
<p>{COMPLETION}</p>
<p><a href="{FORM}">Session 4 exit ticket and feedback · final 10-minute checkpoint</a>. Use evidence from both Labs and wait for the receipt. This anonymous form does not identify attendance.</p>
<h3>Hand checkpoints within the lesson</h3>
<p>{CHECKPOINT}</p>
<p><strong>Planning guide:</strong> {PLANNING}</p>
<h3>Optional further practice</h3>
<p>{OPTIONAL}</p>
<p><a href="../postmidterm-04-appendix.html">Optional session appendix</a></p>
<p><strong>Evidence:</strong> {EVIDENCE}</p>
</section>'''


class ScheduleReader(HTMLParser):
    """Read visible cell text from the already reviewed schedule table."""

    def __init__(self) -> None:
        super().__init__()
        self.rows = []
        self.current_row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.current_row = []
        if tag == 'td':
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.current_row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.current_row:
            self.rows.append(self.current_row)


def updated_metadata(text: str, table: str) -> str:
    """Replace the Session 4 object while preserving all surrounding bytes."""
    doc = json.loads(text)
    decoder = json.JSONDecoder()
    opening = re.search(r'"sessions"\s*:\s*\[', text)
    if opening is None:
        raise ValueError('No sessions array in learning-path.json')
    pos = opening.end()
    found = []
    while True:
        while pos < len(text) and text[pos] in ' \t\r\n,':
            pos += 1
        if text[pos] == ']':
            break
        item, end = decoder.raw_decode(text, pos)
        if item.get('number') == 4:
            found.append((pos, end, item))
        pos = end
    if len(found) != 1:
        raise ValueError('Expected exactly one Session 4 metadata object')
    start, end, item = found[0]
    reader = ScheduleReader()
    reader.feed(table)
    schedule = []
    for row in reader.rows:
        if len(row) != 3:
            raise ValueError('Expected three cells in each reviewed schedule row')
        minutes = re.fullmatch(r'(\d+)\s*[-–]\s*(\d+)\s*min', row[0])
        if minutes is None:
            raise ValueError(f'Unexpected study minutes: {row[0]!r}')
        schedule.append([int(minutes[1]), int(minutes[2]), row[1], row[2]])
    if len(schedule) != 8 or schedule[0][:2] != [0, 20] or schedule[-1][:2] != [170, 180]:
        raise ValueError('Reviewed schedule does not have the expected opening/final checkpoint')
    item.update({
        'claim': 'Interpret consistency and stability evidence, then combine phase-equilibrium conditions with model limits and inventory balances.',
        'outcome': 'Interpret consistency and stability evidence, then distinguish pure-solid solubility, finite-inventory sublimation and surface adsorption; independently close gas-solid and gas-adsorbed inventory balances.',
        'deliverable': CORE,
        'preparation': 'Start at week04-video.html#opening-01. Watch Opening 01-14, pause four minutes for R1-R3 at Opening 13, then continue with the six-page worksheet. The questions page is an alternative to the recorded opening or a reference, not additional required reading. Open the Lab guide only when a step names its pages. This independent lesson replaces class during the ECS meeting. Background reading is optional. H1-H4 is optional and adds no required work.',
        'optionalPractice': OPTIONAL,
        'worksheetLabel': 'English worksheet · 6 pages; A-G and I required, H optional',
        'schedule': schedule,
        'completionNote': COMPLETION,
        'assessmentSummary': CORE,
        'assessmentEvidence': EVIDENCE,
        'assessmentCheckpoint': CHECKPOINT,
        'planningNote': PLANNING,
    })
    line_start = text.rfind('\n', 0, start) + 1
    indent = text[line_start:start]
    if indent.strip():
        raise ValueError('Expected the session object on an indented line')
    formatted = json.dumps(item, ensure_ascii=False, indent=2)
    formatted = formatted.replace('\n', '\n' + indent)
    result = text[:start] + formatted + text[end:]
    revised = json.loads(result)
    for before, after in zip(doc['sessions'], revised['sessions'], strict=True):
        if before['number'] != 4:
            assert before == after, 'Another session metadata object changed'
    assert {k:v for k,v in doc.items() if k != 'sessions'} == {
        k:v for k,v in revised.items() if k != 'sessions'}, 'Top-level metadata changed'
    return result


def replace_metadata(path: Path, table: str, check_only: bool) -> dict:
    before = path.read_bytes()
    after = updated_metadata(before.decode('utf-8'), table).encode('utf-8')
    if not check_only and after != before:
        path.write_bytes(after)
    return {'file': 'assets/' + path.name, 'changed': before != after,
            'written': not check_only, 'outside_session4_unchanged': True}


def replace_section(path: Path, replacement: str, check_only: bool) -> dict:
    before = path.read_bytes()
    text = before.decode('utf-8')
    matches = list(SECTION.finditer(text))
    if len(matches) != 1:
        raise ValueError(f'Expected one Session 4 section in {path}')
    start, end = matches[0].span()
    prefix, suffix = text[:start], text[end:]
    after = (prefix + replacement + suffix).encode('utf-8')
    outside_before = (prefix + suffix).encode('utf-8')
    newtext = after.decode('utf-8')
    newmatch = next(SECTION.finditer(newtext))
    outside_after = (newtext[:newmatch.start()] + newtext[newmatch.end():]).encode('utf-8')
    assert outside_before == outside_after, 'Content outside Session 4 changed'
    if not check_only and after != before:
        path.write_bytes(after)
    return {'file': path.name, 'changed': before != after, 'written': not check_only,
            'outside_session4_unchanged': True,
            'outside_session4_sha256': hashlib.sha256(outside_before).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, required=True, help='Website checkout root')
    parser.add_argument('--check-only', action='store_true', help='Validate and show changes without writing')
    args = parser.parse_args()
    site = args.site.expanduser().resolve()
    global PLANNING
    hub = (site / 'teaching/2105603/week04-study.html').read_text()
    timing = re.search(r'<p id="integrated-timing">(.*?)</p>', hub, re.S)
    if timing is None or '@@' in timing[1]:
        raise ValueError('Apply measured combined-video timing to the hub before updating navigation.')
    from html import unescape
    PLANNING = unescape(re.sub(r'<[^>]+>', '', timing[1]))
    table = course_schedule(site)
    labs = site / 'teaching/2105603/labs'
    # Prepare all replacements before any write, and validate their boundaries.
    replacements = [(labs / 'learning-path.html', section_learning(table)),
                    (labs / 'assessments.html', section_assessments())]
    for path, replacement in replacements:
        replace_section(path, replacement, True)
    metadata = labs / 'assets/learning-path.json'
    replace_metadata(metadata, table, True)
    results = [replace_section(path, replacement, args.check_only)
               for path, replacement in replacements]
    results.append(replace_metadata(metadata, table, args.check_only))
    print(json.dumps({'check_only': args.check_only, 'results': results}, indent=2))


if __name__ == '__main__':
    main()
