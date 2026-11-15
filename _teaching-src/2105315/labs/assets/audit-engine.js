/** Lab 01 · data audit engine. Pure functions, no DOM: the page and the Node checks both import it.
 * Data: UCI Air Quality, hourly, 10 Mar 2004 18:00 to 4 Apr 2005 14:00, kept as the exact source text. */

export const MISSING = -200;
export const WINDOW_HOURS = 336;          // 14 days
export const DUPLICATE_ROWS = 3;          // added for the exercise; the source has none
export const EMPTY_TAIL_ROWS = 2;         // the source file ends with 114 empty rows; each export keeps two
export const SENSOR_COLUMN = 'PT08.S1(CO)';

export const DEMOS = {
  spring: { label: 'Demo A · spring 2004', start: '2004-04-22T00:00' },
  winter: { label: 'Demo B · winter 2004', start: '2004-12-02T00:00' },
};

/** FNV-1a, 32 bit. Same input, same data set, on every computer. */
export function hashText(text) {
  let h = 0x811c9dc5;
  for (const ch of String(text)) {
    h ^= ch.codePointAt(0);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

export function normaliseId(id) { return String(id ?? '').replace(/\s+/g, ''); }

export function validStudentId(id) { return /^\d{8,12}$/.test(normaliseId(id)); }

/** Parse a source value: "2,6" -> 2.6, "-200,0" -> -200. */
export function parseValue(text) {
  const t = String(text).trim();
  if (t === '') return NaN;
  const v = Number(t.replace(',', '.'));
  return Number.isFinite(v) ? v : NaN;
}

const pad = (n) => String(n).padStart(2, '0');

/** Hour index -> source-style date and time ("22/04/2004", "05.00.00"). Times are local, as in the source. */
export function stampAt(data, index) {
  const [d, t] = data.start.split('T');
  const [y, m, day] = d.split('-').map(Number);
  const [hh] = t.split(':').map(Number);
  const ms = Date.UTC(y, m - 1, day, hh) + index * 3600e3;
  const s = new Date(ms);
  return {
    date: `${pad(s.getUTCDate())}/${pad(s.getUTCMonth() + 1)}/${s.getUTCFullYear()}`,
    time: `${pad(s.getUTCHours())}.00.00`,
    iso: `${s.getUTCFullYear()}-${pad(s.getUTCMonth() + 1)}-${pad(s.getUTCDate())}T${pad(s.getUTCHours())}:00`,
    hour: s.getUTCHours(),
    day: `${s.getUTCFullYear()}-${pad(s.getUTCMonth() + 1)}-${pad(s.getUTCDate())}`,
  };
}

export function indexOf(data, iso) {
  const [d, t] = data.start.split('T');
  const toMs = (x) => { const [a, b] = x.split('T'); const [y, m, dd] = a.split('-').map(Number); return Date.UTC(y, m - 1, dd, Number(b.slice(0, 2))); };
  return Math.round((toMs(iso) - toMs(`${d}T${t}`)) / 3600e3);
}

/** Window starts allowed for personal data sets: any hour with 14 full days after it (about 9,000 choices,
 * so two students rarely share a window, and windows one hour apart already give different numbers). */
export function windowStarts(data) {
  return data.hours - WINDOW_HOURS + 1;
}

/** Which 14 days and where the repeated rows go. kind: 'spring' | 'winter' | 'student'. */
export function makeVariant(data, kind, studentId = '') {
  if (kind === 'student') {
    const id = normaliseId(studentId);
    if (!validStudentId(id)) throw new Error('Enter your student ID (8 to 12 digits) to load your own data set.');
    const h = hashText(`2105315-lab01|${id}`);
    const startIndex = h % windowStarts(data);
    const dupAt = 24 + ((h >>> 9) % (WINDOW_HOURS - 48));
    return { kind, label: `My data set · ID ${id}`, seedId: id, startIndex, dupAt };
  }
  const demo = DEMOS[kind];
  if (!demo) throw new Error('Unknown data set.');
  return { kind, label: demo.label, seedId: '', startIndex: indexOf(data, demo.start), dupAt: kind === 'spring' ? 101 : 205 };
}

/** Rows of the exported file, as source text, with the repeated block inserted after its original. */
export function buildRows(data, variant) {
  const rows = [];
  for (let k = 0; k < WINDOW_HOURS; k++) {
    const i = variant.startIndex + k, s = stampAt(data, i);
    rows.push({ hourIndex: i, date: s.date, time: s.time, iso: s.iso, hour: s.hour, day: s.day,
      text: data.columns.map((c) => data.text[c][i]) });
  }
  const block = rows.slice(variant.dupAt, variant.dupAt + DUPLICATE_ROWS).map((r) => ({ ...r, repeat: true }));
  rows.splice(variant.dupAt + DUPLICATE_ROWS, 0, ...block);
  return rows;
}

/** The file a student downloads: semicolons, decimal commas, two empty columns, CRLF, empty rows at the end. */
export function toCsv(data, rows) {
  const lines = [['Date', 'Time', ...data.columns, '', ''].join(';')];
  for (const r of rows) lines.push([r.date, r.time, ...r.text, '', ''].join(';'));
  const width = data.columns.length + 4;
  for (let k = 0; k < EMPTY_TAIL_ROWS; k++) lines.push(';'.repeat(width - 1));
  return lines.join('\r\n') + '\r\n';
}

/** What a reader such as pandas.read_csv would make of the text with the chosen settings (simplified). */
export function previewImport(csvText, { sep = ',', decimal = '.', missing = 'none' } = {}) {
  const sepChar = sep === 'semicolon' ? ';' : sep === 'tab' ? '\t' : ',';
  const lines = csvText.split(/\r?\n/).filter((l, k, a) => !(k === a.length - 1 && l === ''));
  const header = lines[0].split(sepChar);
  const body = lines.slice(1).map((l) => l.split(sepChar));
  const columns = header.map((name, j) => {
    const cells = body.map((r) => (r[j] ?? '').trim());
    const filled = cells.filter((c) => c !== '');
    const asNumber = (c) => {
      const t = decimal === 'comma' ? c.replace(',', '.') : c;
      return /^-?\d+(\.\d+)?$/.test(t) ? Number(t) : NaN;
    };
    const numeric = filled.length > 0 && filled.every((c) => Number.isFinite(asNumber(c)));
    const missingCount = cells.filter((c) => c === '' || (missing === 'code' && numeric && asNumber(c) === MISSING)).length;
    return { name: name === '' ? `Unnamed: ${j}` : name, kind: filled.length === 0 ? 'empty' : numeric ? 'number' : 'text', missingCount, cells };
  });
  const allEmptyRows = body.filter((r) => r.every((c) => c.trim() === '')).length;
  return { columnCount: header.length, rowCount: body.length, allEmptyRows, columns };
}

const valuesOf = (data, rows, column) => {
  const j = data.columns.indexOf(column);
  return rows.map((r) => parseValue(r.text[j]));
};

const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;

/** Remove exact repeats (same timestamp and same values), keeping the first copy. */
export function dedupe(rows) {
  const seen = new Set(), out = [];
  for (const r of rows) {
    const key = r.date + '|' + r.time + '|' + r.text.join('|');
    if (!seen.has(key)) { seen.add(key); out.push(r); }
  }
  return out;
}

/** Everything the audit reports, from the student's own rows. */
export function audit(data, rows) {
  const unique = dedupe(rows);
  const columns = data.columns.map((c) => {
    const v = valuesOf(data, unique, c);
    const valid = v.filter((x) => x !== MISSING && Number.isFinite(x));
    return { name: c, unit: data.units[c], missing: v.length - valid.length, share: (v.length - valid.length) / v.length,
      min: valid.length ? Math.min(...valid) : NaN, max: valid.length ? Math.max(...valid) : NaN };
  });
  const byName = Object.fromEntries(columns.map((c) => [c.name, c]));
  let gaps = 0;
  for (let k = 1; k < unique.length; k++) if (unique[k].hourIndex - unique[k - 1].hourIndex !== 1) gaps++;
  const co = valuesOf(data, unique, 'CO(GT)');
  const coValid = co.filter((x) => x !== MISSING);
  const t = byName.T;
  const facts = {
    rowsInFile: rows.length, uniqueRows: unique.length, repeatedRows: rows.length - unique.length,
    emptyColumns: 2, emptyRows: EMPTY_TAIL_ROWS, gaps,
    coMissing: co.length - coValid.length, coMeanValid: mean(coValid), coMeanNaive: mean(co),
    nmhcShare: byName['NMHC(GT)'].share, sensorMissing: byName[SENSOR_COLUMN].missing, tMin: t.min, tMax: t.max,
  };
  const statements = [
    { id: 'decimal', text: 'Numbers are written with a comma as the decimal mark.', truth: true,
      evidence: 'Every decimal value in the file uses a comma, for example 2,6. Read it with decimal=",".' },
    { id: 'code', text: 'Missing readings are stored as the number -200, not as empty cells.', truth: true,
      evidence: `CO(GT) alone has ${facts.coMissing} hours recorded as -200 in your 14 days.` },
    { id: 'dup', text: 'Some rows appear twice.', truth: true,
      evidence: `${facts.repeatedRows} rows repeat an earlier row exactly. The source has none; they were added to your copy to imitate a logger that re-sent data.` },
    { id: 'empty', text: 'The file has empty columns or empty rows that carry no data.', truth: true,
      evidence: `Each line ends with two empty fields (two unnamed columns) and the file ends with ${EMPTY_TAIL_ROWS} empty rows, as in the source export.` },
    { id: 'nmhc', text: 'NMHC(GT) is -200 in more than half of the hours.', truth: facts.nmhcShare > 0.5,
      evidence: `NMHC(GT) is -200 in ${pct(facts.nmhcShare)} of your hours.` },
    { id: 'block', text: 'In some hours the sensor columns (PT08.S1, T, RH) are all -200 together.', truth: facts.sensorMissing > 0,
      evidence: facts.sensorMissing > 0 ? `${facts.sensorMissing} hours have every sensor column at -200, so the whole device was off.` : 'No hour in your 14 days has the sensor columns missing together.' },
    { id: 'gaps', text: 'Timestamps skip one or more hours.', truth: gaps > 0,
      evidence: gaps > 0 ? `${gaps} jumps in time.` : 'After removing the repeated rows, every row is exactly one hour after the previous one.' },
    { id: 'fahrenheit', text: 'Temperature is recorded in degrees Fahrenheit.', truth: false,
      evidence: `Valid T values run from ${fmt(t.min, 1)} to ${fmt(t.max, 1)}. That is a plausible range in °C, and the source documents T in °C.` },
  ];
  return { facts, columns, statements, unique };
}

export function pct(x) { return `${(100 * x).toFixed(1)}%`; }
export function fmt(x, d = 2) { return Number.isFinite(x) ? x.toFixed(d) : '–'; }

/** Share of CO(GT) hours at -200 for each hour of the day. */
export function missingByHour(data, rows, column = 'CO(GT)') {
  const n = Array(24).fill(0), miss = Array(24).fill(0);
  const j = data.columns.indexOf(column);
  for (const r of rows) { n[r.hour]++; if (parseValue(r.text[j]) === MISSING) miss[r.hour]++; }
  return n.map((c, h) => (c ? miss[h] / c : 0));
}

/** The same pattern over the whole year, as the reference line. */
export function missingByHourAll(data, column = 'CO(GT)') {
  const n = Array(24).fill(0), miss = Array(24).fill(0);
  for (let i = 0; i < data.hours; i++) {
    const h = stampAt(data, i).hour; n[h]++;
    if (parseValue(data.text[column][i]) === MISSING) miss[h]++;
  }
  return n.map((c, h) => miss[h] / c);
}

/** Daily mean CO(GT) for days with at least `minHours` valid hours. */
export function dailyMeans(data, unique, minHours) {
  const j = data.columns.indexOf('CO(GT)'), days = new Map();
  for (const r of unique) {
    if (!days.has(r.day)) days.set(r.day, []);
    const v = parseValue(r.text[j]);
    if (v !== MISSING) days.get(r.day).push(v);
  }
  return [...days].map(([day, v]) => ({ day, valid: v.length, mean: v.length ? mean(v) : NaN, reported: v.length >= minHours }));
}

/** The three numbers students check against their own notebook. */
export function notebookReference(facts) {
  return [
    { id: 'co-missing', text: 'Hours where CO(GT) is missing (-200), after removing repeated rows', value: facts.coMissing, tolerance: 0, decimals: 0 },
    { id: 'co-mean', text: 'Mean CO(GT) of the valid hours, mg/m³', value: facts.coMeanValid, tolerance: 0.005, decimals: 2 },
    { id: 'co-naive', text: 'Mean CO(GT) if -200 is averaged as a number (what the AI code prints)', value: facts.coMeanNaive, tolerance: 0.005, decimals: 2 },
  ];
}
