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
    summary: 'Neutral pH with balanced test parameters (Full 12 ML Features)',
    values: {
      ph: 7.2,
      dissolved_oxygen: 7.0,
      bod: 2.0,
      turbidity: 3.0,
      tds: 250,
      electrical_conductivity: 320,
      nitrate: 1.2,
      temperature: 22.0,
      cod: 10.0,
      ammonia_n: 0.2,
      chlorides: 25.0,
      sulphate: 30.0,
      fecal_coliform: 20.0,
      total_coliform: 50.0,
    },
    notes:
      'Illustrative test input: pH 7.2, DO 7.0 mg/L, BOD 2.0 mg/L, Turbidity 3.0 NTU, TDS 250 mg/L, with all 12 ML parameters.',
  },
  {
    id: 'sample-b',
    name: 'Sample B',
    label: 'Sample B — Illustrative Test Sample',
    tag: 'DEMO',
    summary: 'Acidic pH with elevated turbidity and organic load (Full 12 ML Features)',
    values: {
      ph: 5.2,
      dissolved_oxygen: 3.0,
      bod: 8.0,
      turbidity: 25.0,
      tds: 900,
      electrical_conductivity: 1100,
      nitrate: 6.5,
      temperature: 26.5,
      cod: 45.0,
      ammonia_n: 2.5,
      chlorides: 180.0,
      sulphate: 150.0,
      fecal_coliform: 1200.0,
      total_coliform: 3500.0,
    },
    notes:
      'Illustrative test input: pH 5.2, DO 3.0 mg/L, BOD 8.0 mg/L, Turbidity 25.0 NTU, TDS 900 mg/L, with all 12 ML parameters.',
  },
  {
    id: 'sample-c',
    name: 'Sample C',
    label: 'Sample C — Illustrative Test Sample',
    tag: 'DEMO',
    summary: 'Slightly alkaline pH with moderate solids (Full 12 ML Features)',
    values: {
      ph: 8.0,
      dissolved_oxygen: 6.0,
      bod: 3.0,
      turbidity: 5.0,
      tds: 400,
      electrical_conductivity: 480,
      nitrate: 2.8,
      temperature: 24.0,
      cod: 22.0,
      ammonia_n: 0.8,
      chlorides: 75.0,
      sulphate: 65.0,
      fecal_coliform: 180.0,
      total_coliform: 450.0,
    },
    notes:
      'Illustrative test input: pH 8.0, DO 6.0 mg/L, BOD 3.0 mg/L, Turbidity 5.0 NTU, TDS 400 mg/L, with all 12 ML parameters.',
  },
]

export const INCOMPLETE_SAMPLE = {
  id: 'sample-incomplete',
  name: 'Incomplete Sample',
  label: 'Incomplete Test Sample (Missing Parameters)',
  tag: 'DEMO',
  summary: 'Only pH provided; other parameters omitted to test incomplete handling',
  values: {
    ph: 7.2,
    dissolved_oxygen: null,
    bod: null,
    turbidity: null,
    tds: null,
    electrical_conductivity: null,
    nitrate: null,
    temperature: null,
    cod: null,
    ammonia_n: null,
    chlorides: null,
    sulphate: null,
    fecal_coliform: null,
    total_coliform: null,
  },
  notes:
    'Used to verify that missing core measurements correctly produce an INCONCLUSIVE classification and an INCOMPLETE_FEATURES status from the backend ML service.',
}
