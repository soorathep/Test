"""Reapply course lab links after copying newly rendered books into the site."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT.parents[2]
for id,meta in json.loads((ROOT/'scripts/chapter_metadata.json').read_text()).items():
    vol=int(id[1]);page=SITE/f'teaching/2105623/books/volume-{vol}/chapters'/meta['file']
    s=page.read_text()
    s=re.sub(r'\n<nav class="workbook-lab-link".*?</nav>\n','\n',s,flags=re.S)
    link=f'\n<nav class="workbook-lab-link" aria-label="Interactive companion" style="padding:12px 0;border-bottom:1px solid #ddd;margin-bottom:18px"><a href="../../../labs/?lab={id}">Explore this problem in the Interactive Lab →</a></nav>\n'
    s,count=re.subn(r'(<main\b[^>]*>)',lambda m:m.group(1)+link,s,count=1)
    assert count==1,page
    page.write_text(s)
print('Linked all 47 rendered chapters to their own experiment.')
