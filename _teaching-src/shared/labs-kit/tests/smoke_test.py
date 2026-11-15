"""Shared browser smoke test for SKH interactive labs (one copy for every course).

Each course keeps a short wrapper that passes its published folder and lab list:

    pip install playwright && python3 -m playwright install chromium
    python3 _teaching-src/<course>/labs-next/tests/smoke_test.py

or call this file directly from the repository root:

    python3 _teaching-src/shared/labs-kit/tests/smoke_test.py --base /teaching/<course>/<folder>/ lab1 lab2 ...

Page conventions the test relies on: the main action button has class `calculate-button`, starter
cases have `data-case`, the view switch uses radio inputs named `lab-mode` (values `core`, `graduate`),
investigation buttons in `.graduate-section` have ids starting with `run-`, concept questions use
`.concept-question` with a textarea and a details element, and pages with student details use the
ids `student-first-name`, `student-last-name`, `student-id` and a "Download my study" button.

For every lab it loads the page, runs the main calculation, loads each starter case,
runs every graduate investigation, checks that a concept answer stays closed until the
student has written something, downloads and reopens a study with student details (pages that have them), and
checks that the page fits a 375 px phone screen.
Any JavaScript error, failed check or horizontal overflow makes the script exit with 1.
"""
import argparse
import asyncio
import functools
import http.server
import pathlib
import sys
import threading

from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


async def click_main(page):
    button = page.locator('.calculate-button').first
    for _ in range(40):
        if await button.is_enabled():
            await button.click()
            await page.wait_for_timeout(500)
            return True
        await page.wait_for_timeout(250)
    return False


async def check_submission(browser, url, lab):
    """Download a study with and without student details, then reopen it in a fresh browser."""
    import json
    problems, errors = [], []
    ctx = await browser.new_context(accept_downloads=True)
    page = await ctx.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    await page.goto(url + lab + '.html')
    await page.wait_for_timeout(700)
    if not await page.locator('#student-id').count():
        await ctx.close()
        return []
    await click_main(page)
    export = page.locator('button', has_text='Download my study').first
    for _ in range(40):
        if await export.is_enabled():
            break
        await page.wait_for_timeout(250)
    async def download():
        async with page.expect_download() as info:
            await export.click()
        d = await info.value
        return d.suggested_filename, json.loads(pathlib.Path(await d.path()).read_text())
    name, rec = await download()
    if '_' in name or any(rec.get('student', {}).values()):
        problems.append('blank download carried student details: ' + name)
    await page.fill('#student-first-name', 'Somchai')
    await page.fill('#student-last-name', 'Jaidee')
    await page.fill('#student-id', '6712345621')
    name, rec = await download()
    if not name.endswith('_6712345621_Somchai_Jaidee.json'):
        problems.append('file name lacks student details: ' + name)
    if rec.get('student') != {'firstName': 'Somchai', 'lastName': 'Jaidee', 'studentId': '6712345621'}:
        problems.append('student block missing from the file')
    saved = pathlib.Path('/tmp') / name
    saved.write_text(json.dumps(rec))
    await ctx.close()
    ctx = await browser.new_context()
    page = await ctx.new_page()
    page.on('pageerror', lambda e: errors.append('reopen: ' + str(e)))
    await page.goto(url + lab + '.html')
    await page.wait_for_timeout(900)
    await page.locator('input[type="file"][accept*="json"]').first.set_input_files(str(saved))
    await page.wait_for_timeout(1500)
    if await page.input_value('#student-id') != '6712345621':
        problems.append('reopened study did not restore the student details')
    status = ' '.join(await page.locator('[role="status"], [role="alert"]').all_inner_texts()).lower()
    if 'not a' in status or 'invalid' in status or 'could not' in status:
        problems.append('reopen reported: ' + status[:160])
    await ctx.close()
    return problems + ['JS error: ' + e for e in errors]


async def check_lab(browser, url, lab):
    problems, errors = [], []
    page = await browser.new_page(viewport={'width': 1280, 'height': 900})
    page.on('pageerror', lambda e: errors.append(str(e)))
    await page.goto(url + lab + '.html')
    await page.wait_for_timeout(700)
    if not await click_main(page):
        problems.append('main calculation button never became enabled')
    for case in await page.locator('[data-case]').all():
        if await case.is_visible():
            await case.click()
            await click_main(page)
    if await page.locator('input[name="lab-mode"][value="graduate"]').count():
        await page.check('input[name="lab-mode"][value="graduate"]')
        await click_main(page)
        for run in await page.locator('.graduate-section button[id^="run-"], [id^="g2-run-"]').all():
            if await run.is_visible() and await run.is_enabled():
                await run.click()
                await page.wait_for_timeout(600)
        await page.check('input[name="lab-mode"][value="core"]')
    question = page.locator('.concept-question').first
    if await question.count():
        await question.locator('summary').click()
        if await question.locator('details').evaluate('d => d.open'):
            problems.append('concept explanation opened before an answer was written')
        await question.locator('textarea').fill('A full-sentence answer written before comparing with the explanation.')
        await question.locator('summary').click()
        if not await question.locator('details').evaluate('d => d.open'):
            problems.append('concept explanation did not open after an answer was written')
    phone = await browser.new_page(viewport={'width': 375, 'height': 800})
    phone.on('pageerror', lambda e: errors.append('phone: ' + str(e)))
    await phone.goto(url + lab + '.html')
    await phone.wait_for_timeout(500)
    await click_main(phone)
    width = await phone.evaluate('document.documentElement.scrollWidth')
    if width > 375:
        problems.append(f'page is {width}px wide on a 375px phone')
    await page.close()
    await phone.close()
    return problems + ['JavaScript error: ' + e for e in errors]


async def run(base, labs):
    server = serve()
    url = f'http://127.0.0.1:{server.server_address[1]}{base}'
    failed = False
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for lab in labs:
            problems = await check_lab(browser, url, lab) + await check_submission(browser, url, lab)
            print(('FAIL ' if problems else 'ok   ') + lab + ('' if not problems else ': ' + '; '.join(problems)))
            failed = failed or bool(problems)
        await browser.close()
    server.shutdown()
    return failed


def main(base=None, labs=None):
    if base is None:
        parser = argparse.ArgumentParser(description='Smoke-test published lab pages at desktop and 375 px widths.')
        parser.add_argument('--base', required=True, help='published folder, for example /teaching/2105603/preview-2027/')
        parser.add_argument('labs', nargs='+', help='lab page names without .html')
        args = parser.parse_args()
        base, labs = args.base, args.labs
    if not base.endswith('/'):
        base += '/'
    sys.exit(1 if asyncio.run(run(base, labs)) else 0)


if __name__ == '__main__':
    main()
