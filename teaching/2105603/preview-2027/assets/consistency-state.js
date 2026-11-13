import { validateData } from './case-state.js?v=review-1';
import { analyze, normalizeSettings, normalizeBounds, normalizeRequests, runGraduate } from './consistency-graduate.js';
export { DEFAULT_SETTINGS, DEFAULT_BOUNDS, DEFAULT_REQUESTS, analyze, normalizeSettings, normalizeBounds, normalizeRequests, runGraduate } from './consistency-graduate.js';

export const STUDY_SCHEMA = 'skh-thermo-consistency/1';
export const defaultNotes = () => ({ assumptions: '', uncertainty: '', evidence: '', decision: '' });
export const copy = value => JSON.parse(JSON.stringify(value));
const record = value => value && typeof value === 'object' && !Array.isArray(value);
function normalizeNotes(raw = {}) {
  if (!record(raw)) throw new Error('The saved analysis notes are invalid.');
  const notes = { ...defaultNotes(), ...raw };
  for (const key of Object.keys(defaultNotes())) {
    if (typeof notes[key] !== 'string' || notes[key].length > 15000) throw new Error('A saved analysis note is invalid or too long.');
  }
  return Object.fromEntries(Object.keys(defaultNotes()).map(key => [key, notes[key]]));
}
function context(data) {
  return JSON.stringify({ id: data.id, version: data.version,
    properties: data.properties.map(({ name, A, B, C, rangeK }) => ({ name, A, B, C, rangeK })),
    nrtl: data.nrtl,
    datasets: data.datasets.map(({ pressureKPa, rows }) => ({ pressureKPa,
      rows: rows.map(({ PkPa, T, x, y }) => ({ PkPa, T, x, y })) })) });
}
function normalizeRecord(raw, data, comparison = false) {
  if (!record(raw)) throw new Error('The study record is invalid.');
  const settings = normalizeSettings(raw.settings), bounds = normalizeBounds(raw.bounds),
    notes = normalizeNotes(raw.notes), graduateRequested = normalizeRequests(raw.graduateRequested);
  const modelRequested = raw.modelRequested ?? false;
  if (typeof modelRequested !== 'boolean') throw new Error('The saved modeling-test choice is invalid.');
  let name;
  if (comparison) {
    if (typeof raw.name !== 'string' || !raw.name.trim() || raw.name.length > 120) throw new Error('Each saved comparison needs a short name.');
    name = raw.name.trim();
  }
  const analysis = analyze(settings, data), graduate = runGraduate(data, settings, bounds, graduateRequested);
  return { ...(comparison ? { name } : {}), settings, bounds, notes, modelRequested, graduateRequested, analysis, graduate };
}
export function normalizeStudy(raw, suppliedData) {
  const data = validateData(suppliedData);
  if (!record(raw)) throw new Error('Choose a valid saved consistency study.');
  if (raw.schema !== undefined && raw.schema !== STUDY_SCHEMA) throw new Error('This file belongs to another lab or an unsupported study version. Open original Lab 03 exports in the original interface.');
  if (raw.sourceContext !== undefined && raw.sourceContext !== context(data)) throw new Error('The saved source measurements or property context differ from this version. Keep your file and open the matching lab version.');
  if (!Array.isArray(raw.comparisons ?? [] ) || (raw.comparisons ?? []).length > 60) throw new Error('The comparison list is invalid or exceeds 60 records.');
  const current = normalizeRecord(raw, data);
  const comparisons = (raw.comparisons ?? []).map(entry => normalizeRecord(entry, data, true));
  return { schema: STUDY_SCHEMA, sourceContext: context(data), ...current, comparisons };
}
function plainRecord(entry, comparison = false) {
  return { ...(comparison ? { name: entry.name } : {}), settings: entry.settings, bounds: entry.bounds,
    notes: entry.notes, modelRequested: entry.modelRequested, graduateRequested: entry.graduateRequested };
}
export function serializeStudy(raw, data) {
  const study = normalizeStudy(raw, data);
  return JSON.stringify({ schema: STUDY_SCHEMA, sourceContext: study.sourceContext,
    ...plainRecord(study), comparisons: study.comparisons.map(entry => plainRecord(entry, true)),
    calculationPolicy: 'Derived diagnostics and investigations are recalculated on opening; requested modeling fits run again using the fixed source data.' }, null, 2);
}
export function parseStudy(text, data) {
  if (typeof text !== 'string' || text.length > 5000000) throw new Error('Choose a JSON consistency study smaller than 5 MB.');
  let raw;
  try { raw = JSON.parse(text); } catch { throw new Error('The selected file is not valid JSON. Your current study is unchanged.'); }
  if (!record(raw) || raw.schema !== STUDY_SCHEMA) throw new Error('Choose a saved 2027 Lab 03 study. Other lab files and original Lab 03 result exports cannot be restored here.');
  return normalizeStudy(raw, data);
}
