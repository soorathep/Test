/** SKH interactive labs: student details and the downloaded study file (one copy for every course).
 *
 * The page carries three inputs with the ids student-first-name, student-last-name and student-id.
 * The study file is JSON with a `student` block first; the file name carries the details:
 *   2105315-lab01-audit.json -> 2105315-lab01-audit_6712345621_Somchai_Jaidee.json
 *
 * Use from a course module:
 *   import { initStudentFields, readStudent, withStudent, studentFileName, downloadJson, readJsonFile } from '/teaching/shared/labs-kit/submission.js';
 *   initStudentFields({ storeKey: 'skh-<course>-student' });
 */
const FIELDS = { firstName: 'student-first-name', lastName: 'student-last-name', studentId: 'student-id' };
let STORE = null;

const field = (id) => document.getElementById(id);

export function readStudent() {
  const out = {};
  for (const [key, id] of Object.entries(FIELDS)) out[key] = (field(id)?.value || '').trim().slice(0, 80);
  return out;
}

export function fillStudent(values) {
  for (const [key, id] of Object.entries(FIELDS)) {
    const el = field(id);
    if (el && typeof values?.[key] === 'string') el.value = values[key].slice(0, 80);
  }
  remember();
}

function remember() {
  if (!STORE) return;
  try { localStorage.setItem(STORE, JSON.stringify(readStudent())); } catch { /* storage unavailable */ }
}

/** Adds the student block to a study record before it is saved. */
export function withStudent(record) {
  remember();
  return { student: readStudent(), ...record };
}

export function studentFileName(name) {
  const s = readStudent();
  const parts = [s.studentId, s.firstName, s.lastName]
    .map((p) => p.normalize('NFC').replace(/[\\/:*?"<>|\s_]+/g, '-').replace(/^-+|-+$/g, ''))
    .filter(Boolean);
  return parts.length ? name.replace(/\.json$/i, `_${parts.join('_')}.json`) : name;
}

export function downloadJson(record, name) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url; link.download = name;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function downloadText(text, name, type = 'text/csv') {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const link = document.createElement('a');
  link.href = url; link.download = name;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Read a chosen JSON file; throws a plain-language Error when the file cannot be used. */
export async function readJsonFile(file, maxBytes = 5e6) {
  if (!file) throw new Error('Choose a study file first.');
  if (file.size > maxBytes) throw new Error('This file is larger than a study file can be.');
  try { return JSON.parse(await file.text()); } catch { throw new Error('This file is not valid JSON. Choose a downloaded study file.'); }
}

export function initStudentFields({ storeKey } = {}) {
  if (!storeKey) throw new Error('initStudentFields needs a storeKey so courses do not share stored details.');
  STORE = storeKey;
  try { fillStudent(JSON.parse(localStorage.getItem(STORE) || 'null') || {}); } catch { /* ignore */ }
  for (const id of Object.values(FIELDS)) field(id)?.addEventListener('change', remember);
}
