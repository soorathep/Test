// Render the two review PDFs from the local course preview.
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'));
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const origin=process.env.COURSE_ORIGIN||'http://127.0.0.1:8814';
const browser=await chromium.launch({headless:true,channel:'chrome'});
try {
  const page=await browser.newPage({viewport:{width:1280,height:720}});
  await page.goto(`${origin}/teaching/2105603/week03-gibbs-review.html?print-pdf`);
  await page.waitForFunction(()=>document.querySelector('.pdf-page'));
  await page.evaluate(()=>document.fonts.ready);
  await page.waitForFunction(()=>Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0));
  assert.equal(await page.locator('aside.notes').count(),0);
  assert.equal(await page.locator('.katex-error').count(),0);
  await page.evaluate(origin=>{for(const a of document.querySelectorAll('a[href]'))if(a.href.startsWith(origin+'/'))a.href=a.href.replace(origin+'/','https://www.skhgroup.net/');},origin);
  await page.pdf({path:path.join(root,'teaching/2105603/files/week03-gibbs-review-slides.pdf'),printBackground:true,preferCSSPageSize:true});
  console.log(`Slides exported: ${await page.locator('.pdf-page').count()} pages.`);
  await page.goto(`${origin}/_teaching-src/2105603/prereading/week03-gibbs-review-guide.html`);
  await page.evaluate(()=>document.fonts.ready);
  await page.waitForFunction(()=>Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0));
  await page.pdf({path:path.join(root,'teaching/2105603/files/week03-gibbs-review-guide.pdf'),printBackground:true,preferCSSPageSize:true});
  console.log('Guide exported. Verify four-page pagination, legibility and embedded fonts before publishing.');
} finally {await browser.close();}
