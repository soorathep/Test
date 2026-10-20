// Render already-built public HTML as printable slide artifacts.
import {createRequire} from 'node:module';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
const require=createRequire(import.meta.url);
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'));
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const origin=process.env.COURSE_ORIGIN||'http://127.0.0.1:8813';
const browser=await chromium.launch({headless:true,channel:'chrome'});
try {
  for(const [name,expected] of [['postmidterm-03',44]]){
    const page=await browser.newPage({viewport:{width:1280,height:720}});
    await page.goto(`${origin}/teaching/2105603/${name}.html?print-pdf`);
    await page.waitForFunction(()=>document.querySelector('.pdf-page'),{},{timeout:60000});
    await page.evaluate(()=>document.fonts.ready);
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
    assert.equal(await page.locator('aside.notes').count(),0);
    assert.equal(await page.locator('.katex-error').count(),0);
    // Reveal 5 uses reveal-print, while its bundled legacy print fallback
    // still excludes only print-pdf. Without this compatibility marker,
    // Chromium applies both layouts and fragments the slide wrappers.
    await page.evaluate(()=>document.documentElement.classList.add('print-pdf'));
    // The ?print-pdf page already has Reveal's paginated layout. Keep that
    // geometry rather than activating additional browser print overrides.
    await page.emulateMedia({media:'screen'});
    await page.addStyleTag({content:'.reveal .pause-overlay, .reveal .resume-button { display: none !important; }'});
    const count=await page.locator('.pdf-page').count();
    if(expected!==null)assert.equal(count,expected,'Unexpected split/overflow in slide printing');
    await page.evaluate(origin=>{
      for(const a of document.querySelectorAll('a[href]'))
        if(a.href.startsWith(origin+'/'))a.href=a.href.replace(origin+'/', 'https://www.skhgroup.net/');
    },origin);
    const pdfPath=path.join(root,'teaching/2105603/files',name+'-slides.pdf');
    const titles=await page.locator('.pdf-page section').evaluateAll(slides=>slides.map(s=>s.querySelector('h1,h2')?.textContent.trim()));
    await page.pdf({path:pdfPath,printBackground:true,preferCSSPageSize:true});
    // DOM wrapper counts alone do not detect physical-page fragmentation.
    const check=spawnSync(path.join(os.homedir(),'.venvs/research/bin/python'),['-c',`
import json, re, sys
import pymupdf
pdf=pymupdf.open(sys.argv[1]); titles=json.loads(sys.argv[2])
assert len(pdf)==len(titles), f'{len(pdf)} physical pages for {len(titles)} slides'
norm=lambda s:re.sub(r'\\s+',' ',s).strip()
for i,(page,title) in enumerate(zip(pdf,titles)):
    assert norm(title) in norm(page.get_text()), f'Missing or split heading on page {i+1}: {title}'
    for b in page.get_text('blocks'):
        if b[6]==0:
            assert b[0]>=-1 and b[1]>=-1 and b[2]<=page.rect.width+1 and b[3]<=page.rect.height+1, f'Text outside page {i+1}'
`,pdfPath,JSON.stringify(titles)],{encoding:'utf8'});
    assert.equal(check.status,0,check.stderr||String(check.error||'Physical PDF validation failed'));
    console.log(`${name}: ${count} physical pages, matching headings and page bounds`);
    await page.close();
  }
}finally{await browser.close();}
