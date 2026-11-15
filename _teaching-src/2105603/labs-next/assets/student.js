// Optional student identification for downloaded studies (shared by all labs).
// The three fields are optional: a study downloads with or without them.
const FIELDS = { firstName: 'student-first-name', lastName: 'student-last-name', studentId: 'student-id' };
const STORE = 'thermo-labs-student';

const field = (id) => document.getElementById(id);

export function readStudent() {
  const out = {};
  for (const [key, id] of Object.entries(FIELDS)) out[key] = (field(id)?.value || '').trim().slice(0, 80);
  return out;
}

function fill(values) {
  for (const [key, id] of Object.entries(FIELDS)) {
    const el = field(id);
    if (el && typeof values?.[key] === 'string') el.value = values[key].slice(0, 80);
  }
}

function remember() {
  try { localStorage.setItem(STORE, JSON.stringify(readStudent())); } catch { /* storage unavailable */ }
}

// Adds the student block to a study record (object) before it is saved.
export function withStudent(record) {
  remember();
  return { student: readStudent(), ...record };
}

// Same, for labs that serialize their study to a JSON string first.
export function withStudentJson(text) {
  try { return JSON.stringify(withStudent(JSON.parse(text)), null, 2); } catch { return text; }
}

// lab09-virial-study.json -> lab09-virial-study_6512345621_Somchai_Jaidee.json
export function studentFileName(name) {
  const s = readStudent();
  const parts = [s.studentId, s.firstName, s.lastName]
    .map((p) => p.normalize('NFC').replace(/[\\/:*?"<>|\s]+/g, '-').replace(/^-+|-+$/g, ''))
    .filter(Boolean);
  return parts.length ? name.replace(/\.json$/i, `_${parts.join('_')}.json`) : name;
}

function init() {
  try { fill(JSON.parse(localStorage.getItem(STORE) || 'null')); } catch { /* ignore */ }
  for (const id of Object.values(FIELDS)) field(id)?.addEventListener('change', remember);
  // Reopening a saved study restores the student details it carries.
  for (const input of document.querySelectorAll('input[type="file"][accept*="json"]')) {
    input.addEventListener('change', async () => {
      const file = input.files?.[0];
      if (!file || file.size > 5e6) return;
      try { const rec = JSON.parse(await file.text()); if (rec?.student) { fill(rec.student); remember(); } } catch { /* the lab reports invalid files */ }
    });
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
