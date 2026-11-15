// Writes demo and student-ID data sets as CSV plus the engine's numbers, for engine_vs_pandas.py.
// Usage: node engine_cases.mjs <output folder>
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import * as E from '../assets/audit-engine.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const out = process.argv[2];
const data = JSON.parse(fs.readFileSync(path.join(here, '../assets/data/airquality.json'), 'utf8'));
const ids = ['6712345621', '6630001121', '6531234521', '6400000021', '6798765421', '6612121221'];
const variants = [E.makeVariant(data, 'spring'), E.makeVariant(data, 'winter'), ...ids.map((id) => E.makeVariant(data, 'student', id))];
const cases = variants.map((v, k) => {
  const rows = E.buildRows(data, v), a = E.audit(data, rows);
  fs.writeFileSync(path.join(out, `v${k}.csv`), E.toCsv(data, rows));
  return { k, label: v.label, facts: a.facts, hours: E.missingByHour(data, a.unique), daily: E.dailyMeans(data, a.unique, 18) };
});
fs.writeFileSync(path.join(out, 'facts.json'), JSON.stringify(cases));
