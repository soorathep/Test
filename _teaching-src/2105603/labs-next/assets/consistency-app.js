import {
  DEFAULT_SETTINGS, DEFAULT_BOUNDS, DEFAULT_REQUESTS, defaultNotes, copy,
  normalizeSettings, normalizeBounds, analyze, runGraduate, serializeStudy, parseStudy,
} from './consistency-state.js?v=graduate-1';
import { derivative } from '../../labs/assets/consistency.js';
import { renderMethodPlots, clearMethodPlots } from './consistency-plots.js?v=data-views-1';

const $ = id => document.getElementById(id);
const number = (value, digits = 6) => value == null || !Number.isFinite(value) ? 'Undefined' : Number(value).toLocaleString('en-US', { maximumSignificantDigits: digits });
const statusText = { 'meets-criterion': 'Meets this criterion', 'outside-criterion': 'Outside this criterion', 'not-assessed': 'Not assessed', 'not-applicable': 'Not applicable', 'not-run': 'Not run' };
const sourceNames = { syntheticT: 'Synthetic · 350 K', syntheticP: 'Synthetic · 60 kPa', article60: 'Article · 60 kPa', article80: 'Article · 80 kPa' };
const settingsIds = ['c3-dataset', 'c3-kind', 'c3-amplitude', 'c3-count', 'c3-extension', 'c3-heat'];
const notesKeys = ['assumptions', 'uncertainty', 'evidence', 'decision'];
let data, study = freshStudy(), revision = 0, activeWorker = null, busy = false, operation = null;

function freshStudy() {
  return { settings: copy(DEFAULT_SETTINGS), bounds: copy(DEFAULT_BOUNDS), notes: defaultNotes(),
    graduateRequested: copy(DEFAULT_REQUESTS), modelRequested: false,
    analysis: null, graduate: {}, model: null, modelError: '', comparisons: [] };
}
function cellRow(values) {
  const row = document.createElement('tr');
  for (const value of values) {
    const cell = document.createElement('td');
    if (value instanceof Node) cell.append(value); else cell.textContent = value;
    row.append(cell);
  }
  return row;
}
function rows(id, entries) { $(id).replaceChildren(...entries.map(cellRow)); }
function note(message) { $('c3-status').textContent = message; }
function showError(error, focus = true) {
  $('c3-error').textContent = error.message || String(error); $('c3-error').hidden = false;
  if (focus) $('c3-error').focus();
}
function clearError() { $('c3-error').hidden = true; $('c3-error').textContent = ''; }
function readSettings() {
  return normalizeSettings({ dataset: $('c3-dataset').value, scenario: $('c3-kind').value,
    amplitude: $('c3-amplitude').value, count: $('c3-count').value,
    extension: $('c3-extension').value, heat: $('c3-heat').checked });
}
function readBounds() { return normalizeBounds(Object.fromEntries(['T','P','x','y'].map(key => [key, $('c3-bound-' + key).value]))); }
function readNotes() { return Object.fromEntries(notesKeys.map(key => [key, $('c3-note-' + key).value])); }
function fillFields() {
  const s = study.settings;
  $('c3-dataset').value = s.dataset; $('c3-kind').value = s.scenario;
  $('c3-amplitude').value = s.amplitude; $('c3-count').value = s.count;
  $('c3-extension').value = s.extension; $('c3-heat').checked = s.heat;
  for (const key of ['T','P','x','y']) $('c3-bound-' + key).value = study.bounds[key];
  for (const key of notesKeys) $('c3-note-' + key).value = study.notes[key];
  explainControls();
}
function explainControls() {
  const dataset = $('c3-dataset').value, synthetic = dataset.startsWith('synthetic'), isothermal = dataset === 'syntheticT';
  $('c3-synthetic-controls').hidden = !synthetic; $('c3-endpoint-controls').hidden = synthetic;
  $('c3-amplitude').disabled = !synthetic || $('c3-kind').value === 'clean';
  $('c3-heat').disabled = dataset !== 'syntheticP';
  $('c3-data-origin').textContent = synthetic
    ? 'Model-generated practice data for 2-propanol + water: ' + $('c3-count').value + ' sampled states, including pure endpoints. NRTL supplies the starting activities; Antoine supplies saturation pressures. ' + ($('c3-kind').value === 'clean' ? 'No deliberate activity alteration is applied.' : 'The selected deliberate activity alteration is applied before recalculating the generated VLE states.')
    : 'Published 2-propanol + water measurements from Barbieri, De Guido and Moioli (2024), Table ' + (dataset === 'article60' ? '4 at 60 kPa: 20 measured states, 18 usable activity pairs.' : '5 at 80 kPa: 20 measured states, 17 usable activity pairs.') + ' T, P, x and y are measured; saturation pressures and activity coefficients are calculated. Original rows remain unchanged.';
  $('c3-path-note').textContent = isothermal
    ? 'T = 350 K is fixed. Generated P varies with composition. Synthetic endpoint limits are supplied.'
    : synthetic ? 'P = 60 kPa is fixed. Generated T varies with composition. Synthetic endpoint limits and Hᴱ are supplied.'
      : 'Original P–T–x–y measurements. T varies with composition. Pure endpoints do not determine the absent component’s activity coefficient.';
  $('c3-assumption-summary').textContent = isothermal
    ? 'The starting path holds T fixed. Pressure changes with composition.'
    : 'This path holds P fixed. Temperature changes with composition.';
  $('c3-heat-note').textContent = isothermal ? 'The temperature derivative is zero on this path.'
    : synthetic ? 'Use the generator’s Hᴱ to correct the changing-temperature residual. Uncheck it to inspect the missing-term problem.'
      : 'No independent Hᴱ is available. The real-data differential result remains not assessed.';
  const presets = { 'c3-case-clean': dataset === 'syntheticT' && $('c3-kind').value === 'clean',
    'c3-case-cancel': dataset === 'syntheticT' && $('c3-kind').value === 'cancel',
    'c3-case-isobaric': dataset === 'syntheticP', 'c3-case-article': dataset === 'article60' };
  for (const [id, selected] of Object.entries(presets)) $(id).setAttribute('aria-pressed', String(selected));
  if ($('c3-data-preview').open) renderDataPreview();
}
function renderDataPreview() {
  try {
    if (!data) return;
    const preview = analyze(readSettings(), data).set;
    rows('c3-preview-body', preview.rows.map((row,index)=>[index+1,number(row.T),number(row.PkPa),number(row.x),number(row.y)]));
    $('c3-preview-description').textContent = preview.synthetic
      ? 'Generated practice states for 2-propanol + water, using the selected NRTL-based scenario and Antoine correlations.'
      : preview.name + ': original supplied measurements, in source order. Activity-inference exclusions do not remove rows from this preview.';
    $('c3-preview-status').textContent = 'Showing all ' + preview.rows.length + ' supplied states. ' + (preview.synthetic ? 'These are generated states, not measured observations.' : 'These are measured T–P–x–y states.') + ' Opening this preview does not replace your diagnostic results. Calculate diagnostics separately in Step 1.';
  } catch (error) {
    $('c3-preview-body').replaceChildren();
    $('c3-preview-status').textContent = 'Preview unavailable: ' + error.message + ' Correct the scientific settings first.';
  }
}

function stopWorker() {
  if (!activeWorker) return;
  const old = activeWorker; activeWorker = null; old.worker.terminate(); old.resolve({ error: 'Calculation canceled after a change.' });
}
function setBusy(value, kind = null) { busy = value; operation = value ? kind : null; updateButtons(); }
function updateButtons() {
  const calculated = Boolean(study.analysis), synthetic = calculated && study.analysis.set.synthetic;
  $('c3-model').disabled = !calculated || busy;
  $('c3-save-case').disabled = !calculated || busy || study.comparisons.length >= 60;
  $('c3-export').disabled = !calculated || busy;
  $('c3-run-challenge').disabled = !synthetic || busy;
  $('c3-run-measured').disabled = !calculated || synthetic || busy;
}
function invalidate(message = 'Scientific settings changed. Calculate again; your notes and saved comparisons are retained.') {
  revision++; clearMethodPlots(); stopWorker(); busy = false; operation = null;
  study.analysis = null; study.model = null; study.modelError = ''; study.modelRequested = false;
  study.graduateRequested = copy(DEFAULT_REQUESTS); study.graduate = {};
  $('c3-results').hidden = true; $('c3-result-placeholder').hidden = false;
  $('c3-result-placeholder').textContent = message;
  $('c3-challenge-results').hidden = true; $('c3-measured-results').hidden = true;
  $('c3-challenge-status').textContent = 'Calculate a synthetic case before running this comparison.';
  $('c3-measured-status').textContent = 'Calculate an article data set before running this comparison.';
  $('c3-worked-numeric').replaceChildren(Object.assign(document.createElement('li'), { textContent: 'Calculate the changed case first.' }));
  clearError(); explainControls(); updateButtons(); note(message);
}
function loadCase(settings, label) {
  const notes = readNotes(); invalidate('Starting settings loaded. Press Calculate diagnostics, then compare the methods in Step 2.');
  study.settings = { ...copy(DEFAULT_SETTINGS), ...settings }; study.notes = notes; fillFields();
  $('c3-case-name').value = label;
}
function calculate() {
  try {
    clearError(); const settings = readSettings(), bounds = readBounds(), analysis = analyze(settings, data);
    revision++; stopWorker(); busy = false; operation = null;
    study = { ...study, settings, bounds, notes: readNotes(), analysis, modelRequested: false, model: null, modelError: '', graduateRequested: copy(DEFAULT_REQUESTS), graduate: {} };
    render(); note('Diagnostics calculated. Read Step 2, then run the NRTL modeling test separately.');
  } catch (error) { invalidate('No current result. Correct the settings and calculate again.'); showError(error); }
}
function scorecard(title, result, value) {
  const status = result?.status || 'not-run', card = document.createElement('article');
  card.className = 'scorecard status-' + status;
  const heading = document.createElement('h3'); heading.textContent = title;
  const verdict = document.createElement('strong'); verdict.className = 'criterion-status';
  verdict.textContent = statusText[status] + (result?.conditional ? ' · conditional on endpoint treatment' : '');
  const output = document.createElement('p'); output.textContent = value;
  const scope = document.createElement('small'); scope.textContent = result?.reason || result?.criterion || 'Run the NRTL modeling test for this calculated case.';
  card.append(heading, verdict, output, scope); return card;
}
function renderCards() {
  const { area, local } = study.analysis, model = study.model;
  $('c3-scorecards').replaceChildren(
    scorecard('Isothermal area', area.redlichKister, 'I = ' + number(area.area.signed) + '; D = ' + number(area.area.D) + '%.' + (!area.full ? ' Partial composition interval only.' : '')),
    scorecard('Herington isobaric criterion', area.herington, 'J = ' + number(area.J) + '; D − J = ' + number(area.DminusJ) + (!area.full ? ' (partial area only).' : '.')),
    scorecard('Local differential diagnostic', local, '100 mean |r| = ' + number(local.score) + '. No statistical uncertainty is implied.'),
    scorecard('NRTL modeling capability', model, model ? 'Mean |100 ΔP/P| = ' + number(model.deltaP) + '%; mean |Δy| = ' + number(model.deltaY / 100) + ' mol/mol.' : study.modelError || 'No modeling result yet.')
  );
}
function renderWorked() {
  const { set, local } = study.analysis, index = Math.floor(set.valid.length / 2);
  const a = set.valid[index - 1], b = set.valid[index], c = set.valid[index + 1];
  const triple = [a,b,c].map(row => ({ ...row, g: row.x * row.ln[0] + (1 - row.x) * row.ln[1] }));
  const slope = derivative(...triple, 'g'), localPoint = local.points[index - 1];
  const lines = [
    ...triple.map((row, i) => 'Point ' + (i + 1) + ': x = ' + number(row.x) + '; g = ' + number(row.x) + '(' + number(row.ln[0]) + ') + (1 − ' + number(row.x) + ')(' + number(row.ln[1]) + ') = ' + number(row.g) + '.'),
    'Differentiate the three-point interpolating polynomial at the middle composition: dg/dx = ' + number(slope) + '. ' + (Math.abs((b.x - a.x) - (c.x - b.x)) < 1e-10 ? 'Here the spacing is equal, so this is also (g₃ − g₁)/(x₃ − x₁).' : 'These spacings differ; do not substitute the equally spaced central-difference formula.'),
    'At the middle point, ln(γ₁/γ₂) = ' + number(b.ln[0]) + ' − (' + number(b.ln[1]) + ') = ' + number(b.f) + '.',
    'Raw residual = ' + number(slope) + ' − (' + number(b.f) + ') = ' + number(localPoint.raw) + '. Heat term used = ' + number(localPoint.heat) + '. Final displayed residual = ' + number(localPoint.residual) + '.',
    local.assessed ? 'This is one local value. The score averages absolute residuals over all interior points. A small mean may hide a narrow peak.' : 'The required heat correction is unavailable or disabled, so this numerical raw residual has no consistency verdict.'
  ];
  $('c3-worked-numeric').replaceChildren(...lines.map(text => {
    const li=document.createElement('li');
    // Only fixed scientific labels and formatted finite numbers enter this text.
    li.innerHTML=text.replaceAll('γ₁','γ<sub>1</sub>').replaceAll('γ₂','γ<sub>2</sub>').replaceAll('g₃','g<sub>3</sub>').replaceAll('g₁','g<sub>1</sub>').replaceAll('x₃','x<sub>3</sub>').replaceAll('x₁','x<sub>1</sub>');
    return li;
  }));
}
function renderTables() {
  const { set, local } = study.analysis;
  rows('c3-observation-body', set.rows.map((row,index) => [index + 1, number(row.x),number(row.y),number(row.T),number(row.PkPa),row.ln ? number(row.ln[0]) : '—',row.ln ? number(row.ln[1]) : '—',row.reason || 'Included']));
  rows('c3-residual-body', local.points.map(row => [number(row.x),number(row.raw),number(row.heat),number(row.residual)]));
  $('c3-data-note').textContent = set.synthetic ? set.heatSource + ' Endpoint limits are known from this generator.'
    : 'Original source observations remain unchanged. ' + set.excluded.length + ' rows cannot supply usable activity pairs. The article’s published consistency result (' + set.paper.value + ', ' + set.paper.result + ') is not reproduced by these teaching variants.';
  $('c3-model-detail').textContent = study.model ? JSON.stringify({parameters:study.model.parameters,centeredParameters:study.model.centeredParameters,objective:study.model.objective,converged:study.model.converged,atBound:study.model.atBound,iterations:study.model.iterations,starts:study.model.starts,method:study.model.method},null,2) : study.modelError || 'Modeling test not run.';
}
function renderGraduate() {
  const g = study.graduate || {}, challenge = Boolean(g.controls && g.grids), measured = Boolean(g.endpoints && g.sensitivity);
  $('c3-challenge-results').hidden = !challenge; $('c3-measured-results').hidden = !measured;
  $('c3-challenge-status').textContent = challenge ? 'Controlled errors and three sampling grids calculated for the retained synthetic case.' : 'Calculate a synthetic case, then run the comparisons.';
  $('c3-measured-status').textContent = measured ? g.sensitivity.accepted + ' of 8 measurement-shift scenarios accepted; ' + g.sensitivity.rejected + ' entire scenarios rejected.' : 'Calculate an article data set, then run the comparison.';
  if (challenge) {
    rows('c3-control-body',g.controls.rows.map(r=>[r.label,number(r.I),number(r.D),statusText[r.areaStatus]+(r.conditional?' · conditional':''),number(r.score),number(r.maxResidual),statusText[r.localStatus]]));
    rows('c3-grid-body',g.grids.rows.map((r,i)=>[r.settings.count,number(r.I),number(r.D),number(r.score),i ? 'Δ score = '+number(r.score-g.grids.rows[i-1].score) : 'Coarsest grid']));
  }
  if (measured) {
    rows('c3-endpoint-body',g.endpoints.rows.map(r=>[r.label,number(r.I),number(r.D),number(r.J),number(r.DminusJ),statusText[r.areaStatus]+(r.conditional?' · conditional':'' )]));
    const m=g.sensitivity, summary=[m.nominal,...m.rows];
    $('c3-sensitivity-context').textContent = m.note + ' Current area treatment: ' + study.settings.extension + '.';
    rows('c3-sensitivity-body',summary.map((r,i)=>[r.label,r.status==='rejected'?'Scenario rejected':r.count+' / '+m.nominal.count,r.status==='rejected'?'—':number(r.I),r.status==='rejected'?'—':number(r.D),r.status==='rejected'?'—':number(r.score),r.status==='rejected'?r.reason:i===0?'Nominal reference; local verdict not assessed.':'Same nominal row mask; local verdict not assessed.']));
  }
}
function modelLabel(record) { return record.model ? statusText[record.model.status] : record.modelRequested ? record.modelError || 'Requested; reopen to calculate' : 'Not run'; }
function renderComparisons() {
  $('c3-comparison-empty').hidden = study.comparisons.length > 0; $('c3-comparison-wrap').hidden = study.comparisons.length === 0;
  rows('c3-comparison-body',study.comparisons.map((record,index)=>{
    const a=record.analysis, button=document.createElement('button'); button.type='button';button.textContent='Reopen';button.addEventListener('click',()=>reopenComparison(index));
    return [record.name,sourceNames[record.settings.dataset],number(a.area.area.signed),number(a.area.area.D),number(a.local.score)+' · '+statusText[a.local.status],modelLabel(record),button];
  }));
}
function render() {
  $('c3-results').hidden = !study.analysis; $('c3-result-placeholder').hidden = Boolean(study.analysis);
  if (study.analysis) {
    const {set,area}=study.analysis;
    $('c3-result-title').textContent = set.name + (set.synthetic ? ' · ' + study.settings.scenario : '');
    $('c3-scope').textContent = set.rows.length+' observations; '+set.valid.length+' usable activity pairs; '+set.excluded.length+' excluded. Activity interval: '+number(set.valid[0].x)+' to '+number(set.valid.at(-1).x)+' mol/mol. '+(area.full ? area.conditional?'The full-range area is conditional on an assumed curve.':'Synthetic endpoint limits are known.':'No full-range area claim is available.');
    $('c3-model-status').textContent = study.model ? 'Converged from a five-start fit. '+(study.model.atBound?'At least one parameter is at its bound.':'No parameter is at a bound.') : study.modelError || 'Not run for this calculated case.';
    $('c3-interpretation').textContent = set.synthetic ? (study.settings.scenario==='cancel'?'The added cosine has zero analytical integral, yet changes the local identity. Compare both results and the three-point example. The numerical whole-curve area need not be exactly zero.':study.settings.scenario==='local'?'Inspect the local peak as well as the mean score: a narrow imposed defect can remain below both aggregate thresholds.':'Use the control to separate numerical approximation from a deliberately imposed defect. A criterion met under these assumptions is not blanket validation.') : 'Keep “not assessed” distinct from “outside a criterion.” Missing endpoints or Hᴱ prevent a claim; a model threshold does not identify measurement error as its cause.';
    renderCards();renderWorked();renderTables();renderMethodPlots({analysis:study.analysis,model:study.model,settings:study.settings,data});
  }
  renderGraduate();renderComparisons();updateButtons();
}
function fitInWorker(analysis) {
  stopWorker();
  return new Promise(resolve=>{
    let worker;
    try{worker=new Worker(new URL('./consistency-worker.js',import.meta.url),{type:'module'});}catch(error){resolve({error:'The modeling worker could not start: '+error.message});return;}
    const job={worker,resolve};activeWorker=job;
    const finish=reply=>{if(activeWorker!==job)return;activeWorker=null;worker.terminate();resolve(reply);};
    worker.onmessage=event=>finish(event.data);worker.onerror=()=>finish({error:'The modeling worker failed; no modeling verdict is available.'});
    worker.postMessage({set:analysis.set,properties:data});
  });
}
async function runModel() {
  if(!study.analysis||busy)return;
  clearError();const token=revision,analysis=study.analysis;setBusy(true,'model');$('c3-model-status').textContent='Fitting P and y jointly from five starting guesses…';
  const reply=await fitInWorker(analysis);if(token!==revision)return;
  study.modelRequested=true;study.model=reply.result||null;study.modelError=reply.error||'';setBusy(false);render();note(reply.error?'Modeling result unavailable. Other diagnostics remain available.':'Modeling test finished. Compare its claim with the area and local diagnostics.');
}
function runChallenge() {
  try{if(!study.analysis)return;clearError();study.graduateRequested={...copy(DEFAULT_REQUESTS),controls:true,grids:true};study.graduate=runGraduate(data,study.settings,study.bounds,study.graduateRequested);renderGraduate();note('Controlled-error and grid comparisons calculated. Use these numbers in your conclusion.');}catch(error){showError(error);}
}
function runMeasured() {
  try{if(!study.analysis)return;clearError();study.bounds=readBounds();study.graduateRequested={...copy(DEFAULT_REQUESTS),endpoints:true,sensitivity:true};study.graduate=runGraduate(data,study.settings,study.bounds,study.graduateRequested);renderGraduate();note('Endpoint and common-bias comparisons calculated. Rejected scenarios remain visible.');}catch(error){showError(error);}
}
function saveCase() {
  try{
    if(!study.analysis||busy)return;const name=$('c3-case-name').value.trim();
    if(!name||name.length>120)throw new Error('Enter a case name of 1–120 characters.');
    if(study.comparisons.length>=60)throw new Error('This study already has 60 comparisons. Download it before starting another study.');
    study.notes=readNotes();study.bounds=readBounds();study.comparisons.push(copy({name,settings:study.settings,bounds:study.bounds,notes:study.notes,analysis:study.analysis,graduate:study.graduate,graduateRequested:study.graduateRequested,modelRequested:study.modelRequested,model:study.model,modelError:study.modelError}));renderComparisons();updateButtons();note('Saved “'+name+'” to this study. Download the study to retain it after closing the page.');
  }catch(error){showError(error);}
}
function reopenComparison(index) {
  const record=study.comparisons[index];if(!record)return;
  revision++;stopWorker();busy=false;operation=null;
  study={...study,...copy(record),comparisons:study.comparisons};fillFields();$('c3-case-name').value=record.name;clearError();render();
  note('Reopened “'+record.name+'”. Its saved settings, notes and comparisons are retained.');
}
function exportStudy() {
  try{
    if(!study.analysis||busy)return;clearError();study.notes=readNotes();study.bounds=readBounds();
    const payload=serializeStudy(study,data),url=URL.createObjectURL(new Blob([payload],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='lab03-graduate-consistency-study.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);note('Study downloaded. Open this file here to validate and recalculate its diagnostics and requested fits.');
  }catch(error){showError(error);}
}
async function importStudy(event) {
  const file=event.target.files?.[0];event.target.value='';if(!file)return;
  revision++;stopWorker();const token=revision;setBusy(true,'import');clearError();note('Opening the study and recalculating its evidence. Your current study remains available until validation completes.');
  try{
    if(file.size>5000000)throw new Error('Choose a JSON study smaller than 5 MB.');
    const text=await file.text();if(token!==revision)return;const parsed=parseStudy(text,data);
    for(const record of [parsed,...parsed.comparisons]){
      if(token!==revision)return;
      record.model=null;record.modelError='';
      if(record.modelRequested){const reply=await fitInWorker(record.analysis);if(token!==revision)return;record.model=reply.result||null;record.modelError=reply.error||'';}
    }
    if(token!==revision)return;study=parsed;setBusy(false);fillFields();render();note('Study reopened. Diagnostics, requested investigations and requested modeling fits were recalculated from the retained source context.');
  }catch(error){if(token===revision){setBusy(false);render();showError(error);note('The file was not opened. Your current calculations, notes and saved comparisons are unchanged.');}}
}
function checkRecord() {
  const notes=readNotes(),missing=[];
  if(!study.analysis)missing.push('a calculated current case');
  if(study.comparisons.length<2)missing.push('at least two saved comparisons');
  if(!study.comparisons.some(r=>r.graduateRequested.controls&&r.graduateRequested.grids)&&!study.graduateRequested.controls)missing.push('controlled-error and grid evidence');
  if(!study.comparisons.some(r=>r.graduateRequested.endpoints&&r.graduateRequested.sensitivity)&&!study.graduateRequested.endpoints)missing.push('measured-data endpoint and sensitivity evidence');
  for(const key of notesKeys)if(!notes[key].trim())missing.push('the '+key+' statement');
  note(missing.length?'Record check: add '+missing.join('; ')+'. This checks the record, not the quality of your reasoning.':'The record contains the calculation, comparisons and four written sections. Check the scientific argument yourself; this is not a grade.');
}

  $('c3-data-preview').addEventListener('toggle',()=>{if($('c3-data-preview').open)renderDataPreview();});
  $('c3-preview-link').addEventListener('click',()=>{$('c3-data-preview').open=true;renderDataPreview();});
if (location.hash === '#c3-data-preview') $('c3-data-preview').open = true;

try {
  const response=await fetch('../labs/assets/ipa-water.json');if(!response.ok)throw new Error('The source measurements could not be loaded. Refresh the page to try again.');data=await response.json();
  $('c3-loading').hidden=true;fillFields();$('c3-calculate').disabled=false;note('Starting control loaded. Follow Step 1 and press Calculate diagnostics.');
  $('c3-form').addEventListener('submit',event=>event.preventDefault());

  for(const id of settingsIds)$(id).addEventListener(['c3-amplitude'].includes(id)?'input':'change',()=>invalidate());
  for(const key of ['T','P','x','y'])$('c3-bound-'+key).addEventListener('input',()=>{
    revision++;stopWorker();busy=false;operation=null;study.graduateRequested.sensitivity=false;delete study.graduate.sensitivity;
    $('c3-measured-results').hidden=true;$('c3-measured-status').textContent='Sensitivity assumptions changed. Rerun the measured-data investigation.';$('c3-model-status').textContent=study.model?'A completed modeling result is retained for this baseline.':'Not run for this calculated case.';clearError();updateButtons();note('Sensitivity assumptions changed. Recalculate the measured-data comparison; baseline diagnostics remain available.');
  });
  for(const key of notesKeys)$('c3-note-'+key).addEventListener('input',()=>{
    study.notes=readNotes();
    if(operation==='import'){revision++;stopWorker();setBusy(false);note('Opening canceled because you changed your notes. Your current study and new text are retained.');}
  });
  $('c3-case-clean').addEventListener('click',()=>loadCase({},'A · Consistent isothermal control'));
  $('c3-case-cancel').addEventListener('click',()=>loadCase({scenario:'cancel'},'B · Canceling error at 350 K'));
  $('c3-case-isobaric').addEventListener('click',()=>loadCase({dataset:'syntheticP'},'C · Isobaric control with heat correction'));
  $('c3-case-article').addEventListener('click',()=>loadCase({dataset:'article60'},'D · Measured 60 kPa data'));
  $('c3-calculate').addEventListener('click',calculate);$('c3-model').addEventListener('click',runModel);
  $('c3-run-challenge').addEventListener('click',runChallenge);$('c3-run-measured').addEventListener('click',runMeasured);$('c3-save-case').addEventListener('click',saveCase);$('c3-export').addEventListener('click',exportStudy);$('c3-import').addEventListener('change',importStudy);$('c3-check-record').addEventListener('click',checkRecord);
  updateButtons();
}catch(error){$('c3-loading').textContent=error.message;showError(error,false);}
