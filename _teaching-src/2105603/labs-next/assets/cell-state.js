import * as engine from '../../labs/assets/electrochemistry.js';

export const GUIDED_VERSION = 1;
export const FIXED_TEMPERATURE = 298.15;

export const CASES = {
  baseline: { name: 'Starting case', cLeft: 0.01, cRight: 1, gammaLeft: 1, gammaRight: 1 },
  swap: { name: 'Exchanged concentrations', cLeft: 1, cRight: 0.01, gammaLeft: 1, gammaRight: 1 },
  equal: { name: 'Equal concentrations', cLeft: 1, cRight: 1, gammaLeft: 1, gammaRight: 1 },
  tenfold: { name: 'Tenfold concentration ratio', cLeft: 0.1, cRight: 1, gammaLeft: 1, gammaRight: 1 },
  'same-ratio': { name: 'Same ratio, lower concentrations', cLeft: 0.001, cRight: 0.1, gammaLeft: 1, gammaRight: 1 },
};

export function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function positive(value, label) {
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${label} must be a number greater than zero.`);
  }
  return value;
}

export function calculateCell(values) {
  const cLeft = positive(values.cLeft, 'Left concentration');
  const cRight = positive(values.cRight, 'Right concentration');
  const gammaLeft = positive(values.gammaLeft, 'Left activity coefficient');
  const gammaRight = positive(values.gammaRight, 'Right activity coefficient');
  const input = engine.example(true);
  const header = 'species,nu,phase,atoms,charge,value,gamma\n';
  input.left = `${header}M2+,-1,solute,M:1,2,${cLeft},${gammaLeft}\nM,1,solid,M:1,0,1,1`;
  input.right = `${header}M2+,-1,solute,M:1,2,${cRight},${gammaRight}\nM,1,solid,M:1,0,1,1`;
  input.source = 'Synthetic identical M2+/M electrodes in separate compartments. Concentrations in mol/L and supplied activity coefficients; c°=1 mol/L. Pure metals present; liquid junction potential assumed zero.';
  return engine.calculate(input);
}

export function valuesFromInput(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    throw new Error('The study needs a calculator input object.');
  }
  engine.calculate(input);
  const fixed = input.T === FIXED_TEMPERATURE && input.potentialT === FIXED_TEMPERATURE
    && input.Eleft === 0 && input.Eright === 0 && input.nLeft === 2 && input.nRight === 2
    && input.cStandard === 1 && input.mode === 'concentration';
  if (!fixed) {
    throw new Error('This study uses cell settings outside this guided concentration-cell activity. Open it in the original Lab 13.');
  }

  const readHalf = (text) => {
    const species = engine.half(text, 2, 'concentration', 1).species;
    const ion = species.find((item) => item.name === 'M2+');
    const metal = species.find((item) => item.name === 'M');
    const isOneMetalAtom = (item) => item && Object.keys(item.atoms).length === 1 && item.atoms.M === 1;
    const compatible = species.length === 2 && isOneMetalAtom(ion) && isOneMetalAtom(metal)
      && ion.nu === -1 && ion.phase === 'solute' && ion.charge === 2
      && metal.nu === 1 && metal.phase === 'solid' && metal.charge === 0
      && metal.value === 1 && metal.gamma === 1;
    if (!compatible) {
      throw new Error('This study uses different species or half-reactions. Open it in the original Lab 13.');
    }
    return { concentration: ion.value, gamma: ion.gamma };
  };
  const left = readHalf(input.left);
  const right = readHalf(input.right);
  return { cLeft: left.concentration, cRight: right.concentration, gammaLeft: left.gamma, gammaRight: right.gamma };
}

function prediction(value) {
  if (value === undefined || value === '') return '';
  if (!['positive', 'zero', 'negative'].includes(value)) {
    throw new Error('The study contains an unrecognized prediction.');
  }
  return value;
}

function name(value, fallback) {
  if (value === undefined || value === '') return fallback;
  if (typeof value !== 'string' || value.length > 120) {
    throw new Error('Each case needs a short text name.');
  }
  return value.trim() || fallback;
}

export function parseStudy(text) {
  let study;
  try {
    study = JSON.parse(text);
  } catch {
    throw new Error('The file is not valid JSON. Choose a downloaded calculator study.');
  }
  if (!study || study.kind !== 'electrochemistry' || !study.input) {
    throw new Error('Choose a calculator study downloaded from this activity or the original Lab 13.');
  }
  if (study.guidedVersion !== undefined && study.guidedVersion !== GUIDED_VERSION) {
    throw new Error('This study uses a newer guided format. Open it with the version that created it.');
  }
  const values = valuesFromInput(study.input);
  const savedCases = study.comparisonCases === undefined ? [] : study.comparisonCases;
  if (!Array.isArray(savedCases)) {
    throw new Error('The comparison cases in this file are invalid.');
  }
  const cases = savedCases.map((saved, index) => {
    if (!saved || !saved.input) throw new Error(`Comparison case ${index + 1} has no calculator inputs.`);
    const caseValues = valuesFromInput(saved.input);
    return {
      name: name(saved.name, `Case ${index + 1}`),
      prediction: prediction(saved.prediction),
      values: caseValues,
      result: calculateCell(caseValues),
    };
  });
  if (study.reflection !== undefined && typeof study.reflection !== 'string') {
    throw new Error('The explanation in this file must be text.');
  }
  return {
    values,
    name: name(study.caseName, 'Opened study'),
    prediction: prediction(study.prediction),
    reflection: study.reflection || '',
    cases,
    originalContext: study.originalContext || { source: study.input.source, reference: study.input.reference },
    result: calculateCell(values),
  };
}

export function makeStudy(current, cases, reflection, originalContext) {
  const study = {
    kind: 'electrochemistry',
    ...copy(current.result),
    guidedVersion: GUIDED_VERSION,
    interface: '2105603-2027-guided-preview',
    exportedAt: new Date().toISOString(),
    caseName: current.name,
    prediction: current.prediction,
    reflection,
    comparisonCases: cases.map((saved) => ({
      name: saved.name,
      prediction: saved.prediction,
      input: copy(saved.result.input),
    })),
  };
  if (originalContext) study.originalContext = copy(originalContext);
  return study;
}

export const R = engine.R;
export const F = engine.F;
