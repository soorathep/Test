"""Validate the spoken script against the published slide order before synthesis."""
from pathlib import Path
import argparse,json,re
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--site',type=Path,default=Path.home()/'Documents/GitHub/Test')
args=parser.parse_args()
folder=Path(__file__).resolve().parent
raw=json.loads((folder/'narration-draft.json').read_text())['slides']
slides=BeautifulSoup((args.site/'teaching/2105603/postmidterm-03.html').read_text(),'html.parser').select('.reveal .slides > section')
assert len(raw)==len(slides)==31
entries=[]
for expected,(r,slide) in enumerate(zip(raw,slides),1):
    assert r['number']==expected and r['slide_id']==slide['id'],(expected,r['slide_id'],slide['id'])
    text=r['narration'].replace('log activities','log activity coefficients')
    assert '\\' not in text and not re.search(r'[\u0e00-\u0e7f]',text)
    title=r['title'];m=re.search(r'(\d+)[–-](\d+) min',title)
    cue=r['pause_instruction']
    cue=re.sub(r'(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])',' ',cue)
    cue=cue.replace('studyminute','study minute')
    entries.append({**r,'id':f'{expected:02d}','slide':expected,'narration':text,'pause_instruction':cue,
                    'activity':r['activity_minutes']>0,
                    'stage_start_minute':int(m[1]) if m else None,'stage_end_minute':int(m[2]) if m else None})
assert all(entries[i-1]['activity'] for i in [4,9,18,21,28,30,31])
(folder/'narration.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
print(f'Validated {len(entries)} slide IDs and order; {sum(len(e["narration"].split()) for e in entries)} spoken words; {sum(e["activity"] for e in entries)} pause points.')
