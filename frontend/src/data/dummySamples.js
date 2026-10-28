/**
 * AquaWatch AI — Predefined Dummy Water Quality Samples for Testing
 *
 * IMPORTANT SCIENTIFIC & COMPLIANCE NOTICE:
 * All values below are purely illustrative test inputs (DEMO data) created
 * specifically for verifying the Test Water page and backend validation pipeline.
 * They are NOT verified measurements from real water bodies, do NOT represent
 * actual geographic locations, and do NOT certify that water is safe to drink.
 */

export const DUMMY_SAMPLES = [
  {
    id: 'sample-a',
    name: 'Sample A',
    label: 'Sample A — Illustrative Test Sample',
    tag: 'DEMO',
    summary: 'Neutral pH with balanced test parameters',
    values: {
      ph: 7.2,
      dissolved_oxygen: 7.0,
      bod: 2.0,
      turbidity: 3.0,
      tds: 250,
      electrical_conductivity: 320,
      nitrate: 1.2,
      temperature: 22.0,
    },
    notes:
      'Illustrative test input: pH 7.2, Dissolved Oxygen 7.0 mg/L, BOD 2.0 mg/L, Turbidity 3.0 NTU, TDS 250 mg/L. Unverified dummy test sample.',
  },
  {
    id: 'sample-b',
    name: 'Sample B',
    label: 'Sample B — Illustrative Test Sample',
    tag: 'DEMO',
    summary: 'Acidic pH with elevated turbidity and BOD test values',
    values: {
      ph: 5.2,
      dissolved_oxygen: 3.0,
      bod: 8.0,
      turbidity: 25.0,
      tds: 900,
      electrical_conductivity: 1100,
      nitrate: 6.5,
      temperature: 26.5,
    },
    notes:
      'Illustrative test input: pH 5.2, Dissolved Oxygen 3.0 mg/L, BOD 8.0 mg/L, Turbidity 25.0 NTU, TDS 900 mg/L. Unverified dummy test sample.',
  },
  {
    id: 'sample-c',
    name: 'Sample C',
    label: 'Sample C — Illustrative Test Sample',
    tag: 'DEMO',
    summary: 'Slightly alkaline pH with moderate solids test values',
    values: {
      ph: 8.0,
      dissolved_oxygen: 6.0,
      bod: 3.0,
      turbidity: 5.0,
      tds: 400,
      electrical_conductivity: 480,
      nitrate: 2.8,
      temperature: 24.0,
    },
    notes:
      'Illustrative test input: pH 8.0, Dissolved Oxygen 6.0 mg/L, BOD 3.0 mg/L, Turbidity 5.0 NTU, TDS 400 mg/L. Unverified dummy test sample.',
  },
]

export const INCOMPLETE_SAMPLE = {
  id: 'sample-incomplete',
  name: 'Incomplete Sample',
  label: 'Incomplete Test Sample (Missing Parameters)',
  tag: 'DEMO',
  summary: 'Only pH provided; DO, BOD, Turbidity & TDS are omitted',
  values: {
    ph: 7.2,
    dissolved_oxygen: null,
    bod: null,
    turbidity: null,
    tds: null,
    electrical_conductivity: null,
    nitrate: null,
    temperature: null,
  },
  notes:
    'Used to verify that missing core measurements correctly produce an INCONCLUSIVE classification from the FastAPI backend.',
}
