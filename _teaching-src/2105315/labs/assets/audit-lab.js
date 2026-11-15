/** Lab 01 · page controller. Calculations are in audit-engine.js; charts in charts.js. */
import * as E from './audit-engine.js';
import { coChart, hoursChart, dailyChart } from './charts.js';
import { initStudentFields, readStudent, fillStudent, withStudent, studentFileName, downloadJson, downloadText, readJsonFile } from '/teaching/shared/labs-kit/submission.js';

const SCHEMA = 'skh-2105315-lab01-audit-v1';
const PAGE_VERSION = '2027.1';
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const state = {
  data: null, variant: null, rows: [], csv: '', result: null, audited: false, plot: 'recorded',
  flags: {}, notebookLocked: false, enteredBeforeAudit: {}, hoursYear: null,
  ext: { hoursRun: false, dailyRun: false },
};

initStudentFields({ storeKey: 'skh-2105315-student' });

/* ---------- Step 1: data set ---------- */
function setCase(kind, { quiet = false } = {}) {
  let variant;
  try { variant = E.makeVariant(state.data, kind, readStudent().studentId); }
  catch (error) { $('id-note').textContent = error.message; $('student-id').focus(); return false; }
  state.variant = variant;
  state.rows = E.buildRows(state.data, variant);
  state.csv = E.toCsv(state.data, state.rows);
  state.result = E.audit(state.data, state.rows);
  state.audited = false;
  state.notebookLocked = false;
  state.enteredBeforeAudit = {};
  state.ext = { hoursRun: false, dailyRun: false };
  for (const b of document.querySelectorAll('[data-case]')) b.setAttribute('aria-pressed', String(b.dataset.case === kind));
  if (!quiet) $('id-note').textContent = kind === 'student' ? 'Your own data set is loaded. Use it for the work you submit.' : '';
  const first = E.stampAt(state.data, variant.startIndex), last = E.stampAt(state.data, variant.startIndex + E.WINDOW_HOURS - 1);
  $('dataset-line').textContent = `${variant.label} · ${first.date} ${first.time.slice(0, 5)} to ${last.date} ${last.time.slice(0, 5)} · ${state.rows.length} data rows · file: ${csvName()}`;
  renderRaw();
  renderImport();
  renderFlags();
  renderNotebook();
  $('results').hidden = true;
  $('flag-score').hidden = true;
  $('hours-figure').hidden = true; $('daily-figure').hidden = true;
  $('hours-readout').textContent = ''; $('daily-readout').textContent = '';
  return true;
}

function csvName() {
  const v = state.variant;
  return v.kind === 'student' ? `air-quality-${v.seedId}.csv` : `air-quality-demo-${v.kind}.csv`;
}

/* ---------- Step 2: raw file and import settings ---------- */
function rawLine(text, n, cls = '') {
  const fields = text.split(';').map((f) => (state.audited && (f === '-200' || f === '-200,0') ? `<mark class="miss">${esc(f)}</mark>` : esc(f)));
  return `<span class="line ${cls}" data-n="${n}">${fields.join(';') || ' '}</span>`;
}

function renderRaw() {
  const lines = state.csv.split('\r\n');
  const parts = lines.slice(0, 8).map((l, k) => rawLine(l, k + 1));
  parts.push('<span class="line more">  </span>');
  if (state.audited) {
    const d = state.variant.dupAt + 1;               // +1 for the header line
    for (let k = d; k < d + 2 * E.DUPLICATE_ROWS; k++) parts.push(rawLine(lines[k], k + 1, k >= d + E.DUPLICATE_ROWS ? 'repeat' : ''));
    parts.push('<span class="line more">  </span>');
  }
  const tail = lines.length - 1;                     // last element is '' after the final CRLF
  for (let k = tail - 3; k < tail; k++) parts.push(rawLine(lines[k], k + 1));
  $('raw-file').innerHTML = parts.join('');
  $('raw-file').classList.toggle('audited', state.audited);
}

function importSettings() { return { sep: $('imp-sep').value, decimal: $('imp-dec').value, missing: $('imp-miss').value }; }

function renderImport() {
  const s = importSettings(), p = E.previewImport(state.csv, s);
  const measured = p.columns.filter((c) => state.data.columns.includes(c.name));
  const asText = measured.filter((c) => c.kind === 'text').map((c) => c.name);
  const lines = [];
  let ready = false;
  if (s.sep !== 'semicolon') {
    lines.push(`The reader finds ${p.columnCount} column${p.columnCount === 1 ? '' : 's'} in the header. The file separates fields with semicolons, so the columns are not split correctly (pandas may also stop with a field-count error).`);
  } else if (asText.length) {
    lines.push(`${asText.length} measurement column${asText.length === 1 ? ' is' : 's are'} read as text: ${asText.join(', ')}. A value such as 2,6 is not a number when the decimal mark is a point, so no mean can be taken.`);
  } else if (s.missing !== 'code') {
    lines.push('All measurement columns are read as numbers. The code -200 is a number too, so it will be averaged as a concentration.');
  } else {
    ready = true;
    const co = p.columns.find((c) => c.name === 'CO(GT)');
    lines.push(`Ready to analyse: all ${measured.length} measurement columns are numbers and -200 is read as missing (${co.missingCount} cells in CO(GT), repeated rows included).`);
    lines.push(`Still to handle: ${p.columns.filter((c) => c.kind === 'empty').length} empty columns, ${p.allEmptyRows} empty rows at the end, and any repeated rows.`);
  }
  const box = $('import-verdict');
  box.classList.toggle('ready', ready);
  box.innerHTML = lines.map((l) => `<p>${esc(l)}</p>`).join('');
  $('col-chips').innerHTML = p.columns.map((c) => `<li data-kind="${c.kind}">${esc(c.name.length > 42 ? c.name.slice(0, 40) + '…' : c.name)}</li>`).join('');
  state.importReady = ready;
}

/* ---------- Step 3: flags ---------- */
function renderFlags() {
  $('flag-list').innerHTML = state.result.statements.map((s) => `<li data-flag="${s.id}"><input type="checkbox" id="flag-${s.id}" ${state.flags[s.id] ? 'checked' : ''}><label for="flag-${s.id}">${esc(s.text)}</label><p class="flag-verdict" hidden></p></li>`).join('');
  for (const s of state.result.statements) {
    $(`flag-${s.id}`).addEventListener('change', (e) => { state.flags[s.id] = e.target.checked; });
    $(`flag-${s.id}`).disabled = state.audited;
  }
}

function showFlagVerdicts() {
  let agree = 0;
  for (const s of state.result.statements) {
    const li = document.querySelector(`[data-flag="${s.id}"]`), said = !!state.flags[s.id], ok = said === s.truth;
    agree += ok;
    li.classList.toggle('agree', ok); li.classList.toggle('disagree', !ok);
    const v = li.querySelector('.flag-verdict');
    v.innerHTML = `<strong>${s.truth ? 'True' : 'Not true'} for your file.</strong> You ${said ? 'ticked it' : 'left it unticked'}. ${esc(s.evidence)}`;
    v.hidden = false;
    $(`flag-${s.id}`).disabled = true;
  }
  $('flag-score').textContent = `${agree} of ${state.result.statements.length} statements judged correctly before the audit.`;
  $('flag-score').hidden = false;
  return agree;
}

/* ---------- Step 5: notebook numbers ---------- */
function renderNotebook() {
  const ref = E.notebookReference(state.result.facts);
  const keep = Object.fromEntries(ref.map((r) => [r.id, $(`nb-${r.id}`)?.value ?? '']));
  $('notebook-list').innerHTML = ref.map((r) => `<div class="notebook-item"><label for="nb-${r.id}">${esc(r.text)}</label><input id="nb-${r.id}" type="text" inputmode="decimal" autocomplete="off" value="${esc(keep[r.id])}"><p class="notebook-result" id="nb-${r.id}-result"></p></div>`).join('');
  for (const r of ref) $(`nb-${r.id}`).disabled = state.notebookLocked;
  $('locked-note').textContent = state.notebookLocked
    ? 'Locked by the audit. The submitted file records which numbers you entered before the audit.'
    : 'Enter your numbers before you run the audit. The audit locks them and records whether you entered them first.';
}

function notebookEntries() {
  return E.notebookReference(state.result.facts).map((r) => {
    const raw = ($(`nb-${r.id}`)?.value || '').trim().replace(',', '.');
    const value = raw === '' ? null : Number(raw);
    return { id: r.id, question: r.text, studentValue: Number.isFinite(value) ? value : null, studentText: ($(`nb-${r.id}`)?.value || '').trim(),
      reference: +r.value.toFixed(6), tolerance: r.tolerance,
      withinTolerance: Number.isFinite(value) ? Math.abs(value - r.value) <= r.tolerance + 1e-9 : null,
      enteredBeforeAudit: !!state.enteredBeforeAudit[r.id] };
  });
}

function showNotebookResults() {
  for (const n of notebookEntries()) {
    const out = $(`nb-${n.id}-result`), ref = E.notebookReference(state.result.facts).find((r) => r.id === n.id);
    const refText = ref.value.toFixed(ref.decimals);
    if (n.studentValue === null) { out.className = 'notebook-result'; out.textContent = `No number entered. The audit gives ${refText}.`; }
    else if (n.withinTolerance) { out.className = 'notebook-result match'; out.textContent = `Matches the audit (${refText}).`; }
    else { out.className = 'notebook-result miss'; out.textContent = `The audit gives ${refText}. Find the step in your code that explains the difference.`; }
  }
}

/* ---------- Step 6: audit ---------- */
function runAudit() {
  if (!state.result) return;
  for (const r of E.notebookReference(state.result.facts)) state.enteredBeforeAudit[r.id] = ($(`nb-${r.id}`)?.value || '').trim() !== '';
  state.audited = true;
  state.notebookLocked = true;
  const f = state.result.facts;
  const agree = showFlagVerdicts();
  renderNotebook(); showNotebookResults();
  renderRaw();
  $('result-lead').textContent = `${f.coMissing} of ${f.uniqueRows} hours of CO(GT) are -200. Averaged as numbers, they turn a mean of ${E.fmt(f.coMeanValid)} mg/m³ into ${E.fmt(f.coMeanNaive)} mg/m³.`;
  $('mean-naive').innerHTML = `${E.fmt(f.coMeanNaive)}<span>mg/m³</span>`;
  $('mean-valid').innerHTML = `${E.fmt(f.coMeanValid)}<span>mg/m³</span>`;
  $('valid-note').textContent = `From ${f.uniqueRows - f.coMissing} valid hours, after removing ${f.repeatedRows} repeated rows.`;
  $('audit-body').innerHTML = state.result.columns.map((c) => `<tr><td>${esc(c.name)}</td><td>${esc(c.unit)}</td><td class="${c.share > 0.5 ? 'high' : ''}">${c.missing}</td><td class="${c.share > 0.5 ? 'high' : ''}">${E.pct(c.share)}</td><td>${E.fmt(c.min, 1)}</td><td>${E.fmt(c.max, 1)}</td></tr>`).join('');
  drawCo();
  $('results').hidden = false;
  $('status').textContent = `Audit done: ${agree} of 8 flags judged correctly. Download your study when you have finished the questions.`;
}

function drawCo() {
  const j = state.data.columns.indexOf('CO(GT)');
  const pts = state.result.unique.map((r) => { const v = E.parseValue(r.text[j]); return { value: v, missing: v === E.MISSING, hour: r.hour, date: r.date }; });
  coChart($('co-chart'), pts, state.plot);
  for (const b of document.querySelectorAll('[data-plot]')) b.setAttribute('aria-pressed', String(b.dataset.plot === state.plot));
  $('co-caption').textContent = state.plot === 'recorded'
    ? 'Teal line: CO(GT) as the file records it. Amber points: hours stored as -200. Every drop to -200 is a missing hour drawn as a concentration.'
    : 'Teal line: valid CO(GT) hours. Amber ticks on the time axis: missing hours, where the line breaks.';
}

/* ---------- Step 8: extension ---------- */
function runHours() {
  const mine = E.missingByHour(state.data, state.result.unique);
  state.hoursYear ??= E.missingByHourAll(state.data);
  hoursChart($('hours-chart'), mine, state.hoursYear);
  $('hours-figure').hidden = false;
  const peak = (xs) => xs.reduce((best, v, h) => (v > xs[best] ? h : best), 0);
  const pm = peak(mine), py = peak(state.hoursYear);
  state.ext.hoursRun = true;
  state.ext.hoursPeak = { mine: { hour: pm, share: +mine[pm].toFixed(4) }, year: { hour: py, share: +state.hoursYear[py].toFixed(4) } };
  $('hours-readout').textContent = `Your 14 days: most missing at ${String(pm).padStart(2, '0')}:00 (${E.pct(mine[pm])} of those hours). Whole year: ${String(py).padStart(2, '0')}:00 (${E.pct(state.hoursYear[py])}).`;
}

function runDaily() {
  const min = Number($('min-hours').value);
  const days = E.dailyMeans(state.data, state.result.unique, min);
  dailyChart($('daily-chart'), days);
  $('daily-figure').hidden = false;
  const rep = days.filter((d) => d.reported);
  const meanRep = rep.length ? rep.reduce((a, d) => a + d.mean, 0) / rep.length : NaN;
  state.ext.dailyRun = true;
  state.ext.daily = { minHours: min, reportedDays: rep.length, calendarDays: days.length, meanOfReportedDays: Number.isFinite(meanRep) ? +meanRep.toFixed(4) : null, meanOfValidHours: +state.result.facts.coMeanValid.toFixed(4) };
  $('daily-readout').textContent = `Minimum ${min} h: ${rep.length} of ${days.length} calendar days reported. Mean of reported daily means ${E.fmt(meanRep)} mg/m³; mean of all valid hours ${E.fmt(state.result.facts.coMeanValid)} mg/m³.`;
}

/* ---------- Step 9: study file ---------- */
const answerIds = { 'ai-answer': 'aiCode', 'c-zero': 'zero', 'c-repeats': 'repeats', 'e-hours': 'extHours', 'e-rule': 'extRule' };
function questionText(id) {
  const box = $(id).closest('.concept-question');
  return (box ? box.querySelector('h3') : document.querySelector(`label[for="${id}"]`))?.textContent.trim() ?? id;
}

function makeRecord() {
  const f = state.result.facts;
  return {
    schema: SCHEMA, course: '2105315', lab: 'Lab 01 · Is this file ready for the morning report?', pageVersion: PAGE_VERSION,
    savedAt: new Date().toISOString(), view: document.body.dataset.mode || 'core',
    dataset: { kind: state.variant.kind, seedId: state.variant.seedId, label: state.variant.label, startIndex: state.variant.startIndex,
      start: E.stampAt(state.data, state.variant.startIndex).iso, hours: E.WINDOW_HOURS, repeatedBlockAt: state.variant.dupAt,
      source: `UCI Air Quality, doi:${state.data.source.doi}, ${state.data.source.license}` },
    importSettings: { ...importSettings(), readyForAnalysis: !!state.importReady },
    flags: state.result.statements.map((s) => ({ id: s.id, statement: s.text, ticked: !!state.flags[s.id], ...(state.audited ? { trueForFile: s.truth } : {}) })),
    audited: state.audited,
    audit: state.audited ? { rowsInFile: f.rowsInFile, uniqueRows: f.uniqueRows, repeatedRows: f.repeatedRows, coMissing: f.coMissing,
      coMeanValid: +f.coMeanValid.toFixed(6), coMeanNaive: +f.coMeanNaive.toFixed(6), flagsCorrect: state.result.statements.filter((s) => !!state.flags[s.id] === s.truth).length } : null,
    notebook: notebookEntries().map((n) => (state.audited ? n : { id: n.id, question: n.question, studentText: n.studentText })),
    answers: Object.fromEntries(Object.entries(answerIds).map(([id, key]) => [key, { question: questionText(id), answer: $(id).value }])),
    extension: { ...state.ext, minHoursSetting: Number($('min-hours').value) },
  };
}

function exportStudy() {
  if (!state.result) return;
  const student = readStudent();
  const record = withStudent(makeRecord());
  downloadJson(record, studentFileName('2105315-lab01-audit.json'));
  const warn = state.variant.kind !== 'student' ? ' This file uses a demo data set; load My data set for the work you submit.'
    : student.studentId.replace(/\s+/g, '') !== state.variant.seedId ? ' The student ID in your details differs from the ID that chose this data set.' : '';
  $('status').textContent = `Study downloaded.${warn}`;
}

async function openStudy(file) {
  let rec;
  try { rec = await readJsonFile(file); }
  catch (error) { $('status').textContent = error.message; return; }
  if (rec?.schema !== SCHEMA) { $('status').textContent = 'This file is not a Lab 01 study. Choose the file this page downloaded.'; return; }
  if (rec.student) fillStudent(rec.student);
  const kind = rec.dataset?.kind;
  if (kind === 'student' && rec.dataset.seedId) $('student-id').value = rec.dataset.seedId;
  if (!setCase(kind, { quiet: true })) return;
  if (rec.student) fillStudent(rec.student);
  for (const [k, v] of Object.entries(rec.importSettings || {})) { const el = { sep: 'imp-sep', decimal: 'imp-dec', missing: 'imp-miss' }[k]; if (el && [...$(el).options].some((o) => o.value === v)) $(el).value = v; }
  renderImport();
  state.flags = Object.fromEntries((rec.flags || []).map((f) => [f.id, !!f.ticked]));
  renderFlags();
  for (const n of rec.notebook || []) if ($(`nb-${n.id}`)) $(`nb-${n.id}`).value = n.studentText ?? '';
  for (const [id, key] of Object.entries(answerIds)) if (typeof rec.answers?.[key]?.answer === 'string') $(id).value = rec.answers[key].answer;
  if (Number.isFinite(rec.extension?.minHoursSetting)) { $('min-hours').value = rec.extension.minHoursSetting; $('min-hours-out').textContent = `${rec.extension.minHoursSetting} h`; }
  if (rec.audited) {
    runAudit();
    for (const n of rec.notebook || []) state.enteredBeforeAudit[n.id] = !!n.enteredBeforeAudit;
  }
  if (rec.extension?.hoursRun) runHours();
  if (rec.extension?.dailyRun) runDaily();
  $('status').textContent = `Study reopened: ${state.variant.label}${rec.audited ? ', audit restored' : ''}.`;
}

/* ---------- wiring ---------- */
async function start() {
  try {
    const response = await fetch(new URL('./data/airquality.json', import.meta.url));
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
  } catch (error) {
    $('dataset-line').textContent = `The station record did not load (${error.message}). Reload the page.`;
    return;
  }
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => setCase(b.dataset.case));
  for (const id of ['imp-sep', 'imp-dec', 'imp-miss']) $(id).addEventListener('change', renderImport);
  $('download-csv').addEventListener('click', () => downloadText(state.csv, csvName()));
  $('run-audit').addEventListener('click', runAudit);
  for (const b of document.querySelectorAll('[data-plot]')) b.addEventListener('click', () => { state.plot = b.dataset.plot; drawCo(); });
  $('run-hours').addEventListener('click', runHours);
  $('run-daily').addEventListener('click', runDaily);
  $('min-hours').addEventListener('input', () => { $('min-hours-out').textContent = `${$('min-hours').value} h`; if (state.ext.dailyRun) runDaily(); });
  $('export-study').addEventListener('click', exportStudy);
  $('import-study').addEventListener('change', (e) => { openStudy(e.target.files?.[0]); e.target.value = ''; });
  $('student-id').addEventListener('input', () => {
    if (state.variant?.kind === 'student' && $('student-id').value.replace(/\s+/g, '') !== state.variant.seedId) $('id-note').textContent = 'Your ID changed. Press My data set to load the data set for this ID.';
  });
  setCase('spring');
  for (const id of ['run-audit', 'run-hours', 'run-daily', 'export-study']) $(id).disabled = false;
}

start();
