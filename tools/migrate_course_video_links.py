from pathlib import Path
import json,re,posixpath
from urllib.parse import urlsplit,urlunsplit,urljoin
mapping=json.loads(Path('_data/course_migration.json').read_text())
videos=mapping['videos']; site=Path('_site'); changed=0
for f in site.rglob('*.html'):
 route='/'+f.relative_to(site).as_posix()
 text=f.read_text()
 def fix(m):
  global changed
  url=m[2]; resolved=urlsplit(urljoin('https://www.skhgroup.net'+route,url))
  if resolved.netloc not in ['www.skhgroup.net','skhgroup.net']: return m[0]
  dest=videos.get(resolved.path)
  if not dest:return m[0]
  changed+=1
  return m[1]+dest+('?' + resolved.query if resolved.query else '')+('#'+resolved.fragment if resolved.fragment else '')
 text=re.sub(r"((?:href|src)=[\"'])([^\"']+)",fix,text)
 # Keep old learning-state pages accessible rather than force redirecting users.
 if route.startswith('/teaching/') and (f.name=='index.html' or 'worksheet' in f.name or 'learning-guide' in f.name):
  parts=route.split('/'); code=parts[2]
  if code in mapping['courses']:
   dest=mapping['courses'][code]+route
   notice='<aside style="padding:10px;background:#fff4cc;color:#222;font:14px sans-serif">Course materials have moved. <a href="'+dest+'">Open the current course site</a>. Any notes previously saved in this browser remain on this original page; export them here before moving.</aside>'
   text=re.sub(r'(<body[^>]*>)',lambda m:m[1]+notice,text,count=1)
 f.write_text(text)
print('Migrated video references:',changed)
# Old direct video URLs can still be opened by a person through the 404 route.
p=site/'404.html'
if p.exists():
 text=p.read_text(); script='<script>(function(){const m='+json.dumps(videos)+';const u=m[location.pathname];if(u)location.replace(u+location.search+location.hash)})();</script>'
 p.write_text(text.replace('</head>',script+'</head>',1))
