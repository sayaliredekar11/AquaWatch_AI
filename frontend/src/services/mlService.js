// MOCK ML service. Replace the bodies below with FastAPI calls later.
import { featureImportance } from '../data/mockData'

const delay = (ms) => new Promise((r) => setTimeout(r, ms))

export async function validateSample(sample) {
  await delay(150)
  const required = ['location', 'sampleId', 'date', 'ph', 'do', 'bod', 'cod', 'tds', 'turbidity', 'temperature', 'nitrate', 'phosphate']
  const missing = required.filter((k) => sample[k] === '' || sample[k] === undefined || sample[k] === null)

  const rangeRules = [
    { key: 'ph', name: 'pH', min: 0, max: 14 },
    { key: 'do', name: 'DO', min: 0, max: 20 },
    { key: 'bod', name: 'BOD', min: 0, max: 100 },
    { key: 'cod', name: 'COD', min: 0, max: 500 },
    { key: 'tds', name: 'TDS', min: 0, max: 5000 },
    { key: 'turbidity', name: 'Turbidity', min: 0, max: 100 },
    { key: 'temperature', name: 'Temperature', min: 0, max: 60 },
    { key: 'nitrate', name: 'Nitrate', min: 0, max: 100 },
    { key: 'phosphate', name: 'Phosphate', min: 0, max: 50 },
  ]

  const invalidRanges = []
  rangeRules.forEach(({ key, name, min, max }) => {
    if (sample[key] !== '' && sample[key] !== undefined && sample[key] !== null) {
      const val = Number(sample[key])
      if (isNaN(val) || val < min || val > max) {
        invalidRanges.push(`${name} must be between ${min} and ${max}`)
      }
    }
  })

  const ready = missing.length === 0 && invalidRanges.length === 0

  return {
    missing,
    invalidRanges,
    rangeOk: invalidRanges.length === 0,
    ready,
    dataQuality: ready ? 'Good' : 'Requires Review',
  }
}

export async function predictWQI(sample) {
  await delay(300)
  return {
    wqi: 82.6,
    category: 'GOOD',
    modelVersion: 'Prototype v1',
    featureImportance: [
      { name: 'DO', value: 32 },
      { name: 'BOD', value: 27 },
      { name: 'Turbidity', value: 21 },
      { name: 'pH', value: 10 },
      { name: 'TDS', value: 10 },
    ],
    anomaly: {
      detected: false,
      message: '✓ No significant anomaly detected',
      explanation: 'Current measurements are within the expected historical range.',
    },
  }
}

