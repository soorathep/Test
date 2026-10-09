// Print the bilingual worksheet from the existing local course preview.
import {createRequire} from 'node:module';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url);
const {chromium}=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'));
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const origin=process.env.COURSE_ORIGIN||'http://127.0.0.1:8766';
const browser=await chromium.launch({headless:true,channel:'chrome'});
try {const page=await browser.newPage();await page.goto(origin+'/_teaching-src/2105603/prereading/week02-practice.html');await page.evaluate(()=>document.fonts.ready);await page.pdf({path:path.join(root,'teaching/2105603/files/week02-practice.pdf'),preferCSSPageSize:true,printBackground:true});}finally{await browser.close();}
