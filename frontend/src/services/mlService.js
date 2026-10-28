
import { predictWaterQualityApi } from './api'

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// Validate sample data before sending it to the backend.
export async function validateSample(sample) {
  await delay(100)

  const required = [
    'location',
    'sampleId',
    'date',
    'ph',
    'do',
    'bod',
    'cod',
    'tds',
    'turbidity',
    'nitrate',
    'phosphate',
    'ammonia_n',
    'chlorides',
    'sulphate',
    'fecal_coliform',
    'total_coliform',
  ]

  const missing = required.filter((key) => {
    const value = sample[key]
    return value === '' || value === undefined || value === null
  })

  const rangeRules = [
    { key: 'ph', name: 'pH', min: 0, max: 14 },
    { key: 'do', name: 'Dissolved Oxygen', min: 0, max: 20 },
    { key: 'bod', name: 'BOD', min: 0, max: 100 },
    { key: 'cod', name: 'COD', min: 0, max: 500 },
    { key: 'tds', name: 'TDS', min: 0, max: 5000 },
    { key: 'turbidity', name: 'Turbidity', min: 0, max: 100 },
    { key: 'nitrate', name: 'Nitrate', min: 0, max: 100 },
    { key: 'ammonia_n', name: 'Ammonia Nitrogen', min: 0, max: 100 },
    { key: 'chlorides', name: 'Chlorides', min: 0, max: 5000 },
    { key: 'sulphate', name: 'Sulphate', min: 0, max: 5000 },
    { key: 'fecal_coliform', name: 'Fecal Coliform', min: 0, max: 1000000 },
    { key: 'total_coliform', name: 'Total Coliform', min: 0, max: 1000000 },
  ]

  const invalidRanges = []

  for (const { key, name, min, max } of rangeRules) {
    const value = sample[key]

    if (value === '' || value === undefined || value === null) {
      continue
    }

    const number = Number(value)

    if (!Number.isFinite(number) || number < min || number > max) {
      invalidRanges.push(`${name} must be between ${min} and ${max}`)
    }
  }

  const ready = missing.length === 0 && invalidRanges.length === 0

  return {
    missing,
    invalidRanges,
    rangeOk: invalidRanges.length === 0,
    ready,
    dataQuality: ready ? 'Good' : 'Requires Review',
  }
}

// Send all 12 model features to the trained backend model.
export async function predictWQI(sample) {
  const featureMapping = {
    dissolved_oxygen: sample.do,
    ph: sample.ph,
    bod: sample.bod,
    cod: sample.cod,
    nitrate: sample.nitrate,
    ammonia_n: sample.ammonia_n,
    turbidity: sample.turbidity,
    tds: sample.tds,
    chlorides: sample.chlorides,
    sulphate: sample.sulphate,
    fecal_coliform: sample.fecal_coliform,
    total_coliform: sample.total_coliform,
  }

  const missing = Object.entries(featureMapping)
    .filter(([, value]) => value === '' || value === undefined || value === null)
    .map(([key]) => key)

  if (missing.length > 0) {
    throw new Error(
      `Please provide all 12 measurements before prediction. Missing: ${missing.join(', ')}`
    )
  }

  const invalid = Object.entries(featureMapping)
    .filter(([, value]) => !Number.isFinite(Number(value)))
    .map(([key]) => key)

  if (invalid.length > 0) {
    throw new Error(
      `These measurements must be numeric: ${invalid.join(', ')}`
    )
  }

  const payload = Object.fromEntries(
    Object.entries(featureMapping).map(([key, value]) => [
      key,
      Number(value),
    ])
  )

  // api.js attaches the saved Bearer token when available.
  const result = await predictWaterQualityApi(payload)

  const score = Number(result.prediction)

  if (result.status !== 'SUCCESS' || !Number.isFinite(score)) {
    throw new Error('Backend did not return a valid numeric WQI prediction.')
  }

  return {
    wqi: score,
    category: null,
    modelVersion: result.model_version ?? 'Trained local model',
    featureImportance: [],
    anomaly: null,
  }
}
