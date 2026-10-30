import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FlaskConical,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  Info,
  Loader2,
  FileCode,
  Check,
  Scale,
  AlertOctagon,
  Cpu,
  Sparkles,
  Activity,
} from 'lucide-react'
import { testWaterQualityApi, getWaterBodiesApi } from '../services/api'
import { DUMMY_SAMPLES, INCOMPLETE_SAMPLE } from '../data/dummySamples'

export default function TestWater() {
  const navigate = useNavigate()

  // Selected dummy sample ID ('sample-a', 'sample-b', 'sample-c', 'sample-incomplete', or null for custom)
  const [activeSampleId, setActiveSampleId] = useState(DUMMY_SAMPLES[0].id)
  const [sampleName, setSampleName] = useState(DUMMY_SAMPLES[0].name)
  const [isDemo, setIsDemo] = useState(true)

  // Core baseline measurement inputs (CPCB / IS 10500 baseline)
  const [ph, setPh] = useState(DUMMY_SAMPLES[0].values.ph?.toString() || '7.2')
  const [dissolvedOxygen, setDissolvedOxygen] = useState(
    DUMMY_SAMPLES[0].values.dissolved_oxygen?.toString() || '7.0'
  )
  const [bod, setBod] = useState(DUMMY_SAMPLES[0].values.bod?.toString() || '2.0')
  const [turbidity, setTurbidity] = useState(
    DUMMY_SAMPLES[0].values.turbidity?.toString() || '3.0'
  )
  const [tds, setTds] = useState(DUMMY_SAMPLES[0].values.tds?.toString() || '250')

  // Additional 6 parameters required by the trained ML Decision Tree WQI Model
  const [cod, setCod] = useState(DUMMY_SAMPLES[0].values.cod?.toString() || '10.0')
  const [ammoniaN, setAmmoniaN] = useState(
    DUMMY_SAMPLES[0].values.ammonia_n?.toString() || '0.2'
  )
  const [chlorides, setChlorides] = useState(
    DUMMY_SAMPLES[0].values.chlorides?.toString() || '25.0'
  )
  const [sulphate, setSulphate] = useState(
    DUMMY_SAMPLES[0].values.sulphate?.toString() || '30.0'
  )
  const [fecalColiform, setFecalColiform] = useState(
    DUMMY_SAMPLES[0].values.fecal_coliform?.toString() || '20.0'
  )
  const [totalColiform, setTotalColiform] = useState(
    DUMMY_SAMPLES[0].values.total_coliform?.toString() || '50.0'
  )

  // Optional secondary physical parameters
  const [electricalConductivity, setElectricalConductivity] = useState(
    DUMMY_SAMPLES[0].values.electrical_conductivity?.toString() || '320'
  )
  const [nitrate, setNitrate] = useState(
    DUMMY_SAMPLES[0].values.nitrate?.toString() || '1.2'
  )
  const [temperature, setTemperature] = useState(
    DUMMY_SAMPLES[0].values.temperature?.toString() || '22.0'
  )

  // Optional database persistence state (Default False: isolates dummy testing from real monitoring records)
  const [saveToDb, setSaveToDb] = useState(false)
  const [selectedWaterBodyId, setSelectedWaterBodyId] = useState('')
  const [waterBodies, setWaterBodies] = useState([])
  const [loadingBodies, setLoadingBodies] = useState(false)

  // Submission and real backend response states
  const [submitting, setSubmitting] = useState(false)
  const [clientError, setClientError] = useState(null)
  const [backendError, setBackendError] = useState(null)
  const [backendResponse, setBackendResponse] = useState(null)
  const [showRawJson, setShowRawJson] = useState(false)

  // Load water bodies if user enables save to database
  useEffect(() => {
    if (saveToDb && waterBodies.length === 0) {
      setLoadingBodies(true)
      getWaterBodiesApi(0, 50)
        .then((bodies) => {
          setWaterBodies(bodies || [])
          if (bodies && bodies.length > 0 && !selectedWaterBodyId) {
            setSelectedWaterBodyId(bodies[0].id.toString())
          }
        })
        .catch((err) => {
          console.error('Failed to load water bodies:', err)
        })
        .finally(() => setLoadingBodies(false))
    }
  }, [saveToDb, waterBodies.length, selectedWaterBodyId])

  // Load predefined dummy sample into the form inputs
  const handleLoadSample = (sample) => {
    setActiveSampleId(sample.id)
    setSampleName(sample.name)
    setIsDemo(true)

    setPh(sample.values.ph !== null && sample.values.ph !== undefined ? sample.values.ph.toString() : '')
    setDissolvedOxygen(
      sample.values.dissolved_oxygen !== null && sample.values.dissolved_oxygen !== undefined
        ? sample.values.dissolved_oxygen.toString()
        : ''
    )
    setBod(sample.values.bod !== null && sample.values.bod !== undefined ? sample.values.bod.toString() : '')
    setTurbidity(
      sample.values.turbidity !== null && sample.values.turbidity !== undefined
        ? sample.values.turbidity.toString()
        : ''
    )
    setTds(sample.values.tds !== null && sample.values.tds !== undefined ? sample.values.tds.toString() : '')

    // ML Features
    setCod(sample.values.cod !== null && sample.values.cod !== undefined ? sample.values.cod.toString() : '')
    setAmmoniaN(
      sample.values.ammonia_n !== null && sample.values.ammonia_n !== undefined
        ? sample.values.ammonia_n.toString()
        : ''
    )
    setChlorides(
      sample.values.chlorides !== null && sample.values.chlorides !== undefined
        ? sample.values.chlorides.toString()
        : ''
    )
    setSulphate(
      sample.values.sulphate !== null && sample.values.sulphate !== undefined
        ? sample.values.sulphate.toString()
        : ''
    )
    setFecalColiform(
      sample.values.fecal_coliform !== null && sample.values.fecal_coliform !== undefined
        ? sample.values.fecal_coliform.toString()
        : ''
    )
    setTotalColiform(
      sample.values.total_coliform !== null && sample.values.total_coliform !== undefined
        ? sample.values.total_coliform.toString()
        : ''
    )

    // Secondary
    setElectricalConductivity(
      sample.values.electrical_conductivity ? sample.values.electrical_conductivity.toString() : ''
    )
    setNitrate(sample.values.nitrate ? sample.values.nitrate.toString() : '')
    setTemperature(sample.values.temperature ? sample.values.temperature.toString() : '')

    // Clear previous results and errors
    setClientError(null)
    setBackendError(null)
    setBackendResponse(null)
  }

  // Reset form to blank / custom test state
  const handleReset = () => {
    setActiveSampleId(null)
    setSampleName('Custom Test Sample')
    setIsDemo(true)
    setPh('')
    setDissolvedOxygen('')
    setBod('')
    setTurbidity('')
    setTds('')
    setCod('')
    setAmmoniaN('')
    setChlorides('')
    setSulphate('')
    setFecalColiform('')
    setTotalColiform('')
    setElectricalConductivity('')
    setNitrate('')
    setTemperature('')
    setSaveToDb(false)
    setSelectedWaterBodyId('')
    setClientError(null)
    setBackendError(null)
    setBackendResponse(null)
    setShowRawJson(false)
  }

  // Submit measurements to real FastAPI backend
  const handleSubmit = async (e) => {
    e.preventDefault()
    setClientError(null)
    setBackendError(null)
    setBackendResponse(null)

    // Build payload with null for empty fields to test complete/incomplete evaluation
    const parsedPh = ph !== '' && !isNaN(parseFloat(ph)) ? parseFloat(ph) : null
    const parsedDo = dissolvedOxygen !== '' && !isNaN(parseFloat(dissolvedOxygen)) ? parseFloat(dissolvedOxygen) : null
    const parsedBod = bod !== '' && !isNaN(parseFloat(bod)) ? parseFloat(bod) : null
    const parsedTurbidity = turbidity !== '' && !isNaN(parseFloat(turbidity)) ? parseFloat(turbidity) : null
    const parsedTds = tds !== '' && !isNaN(parseFloat(tds)) ? parseFloat(tds) : null

    // ML Features
    const parsedCod = cod !== '' && !isNaN(parseFloat(cod)) ? parseFloat(cod) : null
    const parsedAmmonia = ammoniaN !== '' && !isNaN(parseFloat(ammoniaN)) ? parseFloat(ammoniaN) : null
    const parsedChlorides = chlorides !== '' && !isNaN(parseFloat(chlorides)) ? parseFloat(chlorides) : null
    const parsedSulphate = sulphate !== '' && !isNaN(parseFloat(sulphate)) ? parseFloat(sulphate) : null
    const parsedFecal = fecalColiform !== '' && !isNaN(parseFloat(fecalColiform)) ? parseFloat(fecalColiform) : null
    const parsedTotal = totalColiform !== '' && !isNaN(parseFloat(totalColiform)) ? parseFloat(totalColiform) : null

    // Secondary
    const parsedEc = electricalConductivity !== '' && !isNaN(parseFloat(electricalConductivity)) ? parseFloat(electricalConductivity) : null
    const parsedNitrate = nitrate !== '' && !isNaN(parseFloat(nitrate)) ? parseFloat(nitrate) : null
    const parsedTemp = temperature !== '' && !isNaN(parseFloat(temperature)) ? parseFloat(temperature) : null

    if (saveToDb && !selectedWaterBodyId) {
      setClientError('Please select a monitored water body if you have opted to persist this record to PostgreSQL.')
      return
    }

    const payload = {
      sample_name: sampleName || 'Test Sample',
      is_demo: isDemo,
      ph: parsedPh,
      dissolved_oxygen: parsedDo,
      bod: parsedBod,
      turbidity: parsedTurbidity,
      tds: parsedTds,
      cod: parsedCod,
      ammonia_n: parsedAmmonia,
      chlorides: parsedChlorides,
      sulphate: parsedSulphate,
      fecal_coliform: parsedFecal,
      total_coliform: parsedTotal,
      electrical_conductivity: parsedEc,
      nitrate: parsedNitrate,
      temperature: parsedTemp,
      save_to_db: saveToDb,
      water_body_id: saveToDb && selectedWaterBodyId ? parseInt(selectedWaterBodyId, 10) : null,
    }

    setSubmitting(true)
    try {
      const result = await testWaterQualityApi(payload)
      setBackendResponse(result)
    } catch (err) {
      setBackendError(err.message || 'Failed to communicate with FastAPI backend server.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-65px)] bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Page Header */}
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-md bg-blue-100 px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-blue-800">
              LAB_AUTHORITY ACCESS
            </span>
            <span className="inline-flex items-center rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
              SAFETY CLASSIFICATION + ML WQI
            </span>
          </div>
          <h1 className="mt-2 text-2xl font-black text-slate-900 sm:text-3xl flex items-center gap-2.5">
            <FlaskConical className="h-7 w-7 text-blue-600" />
            <span>Water Quality Testing & ML WQI Analysis</span>
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Submit water quality test measurements for standard rule-based safety screening (<strong>SAFE</strong>, <strong>HARMFUL</strong>, or <strong>INCONCLUSIVE</strong>) and trained <strong>DecisionTreeRegressor</strong> Water Quality Index (WQI) scoring.
          </p>
        </div>

        {/* Section 1: Predefined Dummy Samples Loader */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
                1. Select Predefined Test Sample
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Click any sample below to load its full 12-feature measurements into the testing form.
              </p>
            </div>
            {activeSampleId && (
              <span className="self-start sm:self-auto text-xs font-semibold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
                Active: {sampleName}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {DUMMY_SAMPLES.map((sample) => {
              const isSelected = activeSampleId === sample.id
              return (
                <div
                  key={sample.id}
                  onClick={() => handleLoadSample(sample)}
                  className={`cursor-pointer rounded-xl border p-4 transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50/60 shadow-sm ring-2 ring-blue-500/20'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-sm text-slate-900">{sample.name}</span>
                        <span className="rounded bg-slate-200 px-1.5 py-0.2 text-[10px] font-bold uppercase text-slate-700">
                          {sample.tag}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-1">{sample.summary}</p>
                    </div>
                    {isSelected ? (
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-white">
                        <Check className="h-3 w-3 stroke-[3]" />
                      </span>
                    ) : null}
                  </div>

                  {/* Sample Parameters Preview */}
                  <div className="mt-3 grid grid-cols-3 gap-1 rounded-lg bg-slate-100/70 p-2 text-center text-[11px] text-slate-700">
                    <div>
                      <span className="text-[10px] text-slate-400 block font-medium">pH</span>
                      <strong className="text-slate-800">{sample.values.ph}</strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-medium">DO</span>
                      <strong className="text-slate-800">{sample.values.dissolved_oxygen}</strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-medium">BOD</span>
                      <strong className="text-slate-800">{sample.values.bod}</strong>
                    </div>
                    <div className="mt-1">
                      <span className="text-[10px] text-slate-400 block font-medium">Turbidity</span>
                      <strong className="text-slate-800">{sample.values.turbidity}</strong>
                    </div>
                    <div className="mt-1">
                      <span className="text-[10px] text-slate-400 block font-medium">COD</span>
                      <strong className="text-slate-800">{sample.values.cod}</strong>
                    </div>
                    <div className="mt-1">
                      <span className="text-[10px] text-slate-400 block font-medium">TDS</span>
                      <strong className="text-slate-800">{sample.values.tds}</strong>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleLoadSample(sample)
                    }}
                    className={`mt-3 w-full rounded-lg py-1.5 text-xs font-semibold transition-colors ${
                      isSelected
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'border border-slate-300 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {isSelected ? 'Loaded into Form' : `Load ${sample.name}`}
                  </button>
                </div>
              )
            })}
          </div>

          {/* Quick-loader for Incomplete Sample to test INCONCLUSIVE */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Need to test missing/incomplete data handling?
            </span>
            <button
              type="button"
              onClick={() => handleLoadSample(INCOMPLETE_SAMPLE)}
              className={`text-xs font-semibold px-3 py-1 rounded-lg border transition-colors ${
                activeSampleId === INCOMPLETE_SAMPLE.id
                  ? 'border-amber-500 bg-amber-50 text-amber-900 ring-1 ring-amber-400'
                  : 'border-slate-300 text-slate-700 hover:bg-slate-100'
              }`}
            >
              Load Incomplete Sample (Tests INCONCLUSIVE)
            </button>
          </div>
        </div>

        {/* Section 2: Form Inputs */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-8 shadow-xs space-y-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
                  2. Water Quality Test Inputs
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Values will be sent to the FastAPI backend endpoint <code>/water-quality/test</code>.
                </p>
              </div>
              <span className="text-xs text-slate-500 font-mono">
                Sample: {sampleName || 'Custom'}
              </span>
            </div>

            {/* Core Required Parameters Grid */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                  Core Screening Parameters (Standard Baseline)
                </h3>
                <span className="text-[11px] text-slate-400">CPCB Class C / IS 10500 Baseline</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
                {/* pH */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    pH (Standard: 6.5 – 8.5)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={ph}
                    onChange={(e) => {
                      setPh(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-medium focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g. 7.2"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">Standard units</span>
                </div>

                {/* Dissolved Oxygen */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    DO (Standard: ≥ 4.0 mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={dissolvedOxygen}
                    onChange={(e) => {
                      setDissolvedOxygen(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-medium focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g. 7.0"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">Dissolved Oxygen</span>
                </div>

                {/* BOD */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    BOD (Standard: ≤ 3.0 mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={bod}
                    onChange={(e) => {
                      setBod(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-medium focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g. 2.0"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">Biochemical O₂</span>
                </div>

                {/* Turbidity */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Turbidity (Std: ≤ 5.0 NTU)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={turbidity}
                    onChange={(e) => {
                      setTurbidity(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-medium focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g. 3.0"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">Clarity index</span>
                </div>

                {/* TDS */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    TDS (Std: ≤ 500 mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={tds}
                    onChange={(e) => {
                      setTds(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-medium focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="e.g. 250"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">Total Dissolved</span>
                </div>
              </div>
            </div>

            {/* Advanced ML Model Parameters */}
            <div className="rounded-xl border border-indigo-200 bg-indigo-50/40 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-indigo-600" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-900">
                    Advanced Model Features (Required for Machine Learning WQI)
                  </h3>
                </div>
                <span className="text-[10px] font-semibold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded">
                  DecisionTreeRegressor (12 Features)
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {/* COD */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    COD (Chemical Oxygen Demand, mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={cod}
                    onChange={(e) => {
                      setCod(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-medium focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g. 10.0"
                  />
                </div>

                {/* Ammonia Nitrogen */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Ammonia Nitrogen (mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={ammoniaN}
                    onChange={(e) => {
                      setAmmoniaN(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-medium focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g. 0.2"
                  />
                </div>

                {/* Chlorides */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Chlorides (mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={chlorides}
                    onChange={(e) => {
                      setChlorides(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-medium focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g. 25.0"
                  />
                </div>

                {/* Sulphate */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Sulphate (mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={sulphate}
                    onChange={(e) => {
                      setSulphate(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-medium focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g. 30.0"
                  />
                </div>

                {/* Fecal Coliform */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Fecal Coliform (MPN/100mL)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={fecalColiform}
                    onChange={(e) => {
                      setFecalColiform(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-medium focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g. 20.0"
                  />
                </div>

                {/* Total Coliform */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Total Coliform (MPN/100mL)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={totalColiform}
                    onChange={(e) => {
                      setTotalColiform(e.target.value)
                      setActiveSampleId(null)
                    }}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-medium focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g. 50.0"
                  />
                </div>
              </div>
            </div>

            {/* Optional Parameters */}
            <div className="rounded-lg bg-slate-50/70 p-4 border border-slate-200/70 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                Optional Secondary Parameters (Informational)
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Electrical Cond. (µS/cm)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={electricalConductivity}
                    onChange={(e) => setElectricalConductivity(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
                    placeholder="320"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Nitrate (mg/L, Std: ≤ 45)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={nitrate}
                    onChange={(e) => setNitrate(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
                    placeholder="1.2"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Temperature (°C)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
                    placeholder="22.0"
                  />
                </div>
              </div>
            </div>

            {/* Explicit Database Persistence Section */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 space-y-3">
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  id="saveToDbToggle"
                  checked={saveToDb}
                  onChange={(e) => setSaveToDb(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="saveToDbToggle" className="text-xs font-semibold text-slate-800 cursor-pointer">
                  <span>Explicit Action: Persist test record into PostgreSQL database</span>
                  <p className="text-slate-500 font-normal mt-0.5">
                    Unchecked by default. Leave unchecked for in-memory testing so dummy samples do not skew real monitoring averages.
                  </p>
                </label>
              </div>

              {saveToDb && (
                <div className="pt-2 pl-7 space-y-2">
                  <label className="text-xs font-semibold text-slate-700 block">
                    Select Target Monitored Water Body *
                  </label>
                  {loadingBodies ? (
                    <div className="h-9 animate-pulse rounded-lg bg-slate-200" />
                  ) : (
                    <select
                      value={selectedWaterBodyId}
                      onChange={(e) => setSelectedWaterBodyId(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-medium"
                      required={saveToDb}
                    >
                      <option value="">-- Choose Water Body --</option>
                      {waterBodies.map((wb) => (
                        <option key={wb.id} value={wb.id}>
                          {wb.name} ({wb.location_name}) — ID #{wb.id}
                        </option>
                      ))}
                    </select>
                  )}
                  <p className="text-[11px] text-amber-700 font-medium">
                    ⚠ Notice: Persisting dummy data will record this measurement in PostgreSQL.
                  </p>
                </div>
              )}
            </div>

            {/* Validation & Backend Error Alerts */}
            {clientError && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5 text-rose-600" />
                <div>
                  <p className="font-bold">Validation Notice</p>
                  <p className="text-xs mt-0.5">{clientError}</p>
                </div>
              </div>
            )}

            {backendError && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5 text-rose-600" />
                <div>
                  <p className="font-bold">Backend Request Failed (FastAPI)</p>
                  <p className="text-xs mt-0.5">{backendError}</p>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset Form</span>
              </button>

              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 transition-colors"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Evaluating with FastAPI Backend...</span>
                  </>
                ) : (
                  <>
                    <FlaskConical className="h-4 w-4" />
                    <span>Submit Measurements for Testing</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Section 3: Prominent Safety Classification Banner & Findings */}
        {backendResponse && (
          <div className="space-y-6">
            {/* Classification Card */}
            <div
              className={`rounded-2xl border-2 p-6 shadow-sm transition-all ${
                backendResponse.classification === 'SAFE'
                  ? 'border-emerald-400 bg-emerald-50/90'
                  : backendResponse.classification === 'HARMFUL'
                  ? 'border-rose-400 bg-rose-50/90'
                  : 'border-amber-400 bg-amber-50/90'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="mt-1">
                    {backendResponse.classification === 'SAFE' ? (
                      <ShieldCheck className="h-10 w-10 text-emerald-600" />
                    ) : backendResponse.classification === 'HARMFUL' ? (
                      <ShieldAlert className="h-10 w-10 text-rose-600" />
                    ) : (
                      <HelpCircle className="h-10 w-10 text-amber-600" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                        WATER SAFETY CLASSIFICATION
                      </span>
                      <span className="text-[10px] font-bold uppercase rounded px-1.5 py-0.5 bg-white/80 border border-slate-300 text-slate-700">
                        {backendResponse.result_type}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-3">
                      <span
                        className={`inline-block px-4 py-1 rounded-lg text-xl font-black tracking-wide shadow-xs ${
                          backendResponse.classification === 'SAFE'
                            ? 'bg-emerald-600 text-white'
                            : backendResponse.classification === 'HARMFUL'
                            ? 'bg-rose-600 text-white'
                            : 'bg-amber-500 text-white'
                        }`}
                      >
                        {backendResponse.classification}
                      </span>
                      <span className="text-sm font-semibold text-slate-800">
                        Sample: {backendResponse.sample_name}
                      </span>
                    </div>
                    <p className="mt-1.5 text-xs text-slate-700 leading-relaxed">
                      {backendResponse.message}
                    </p>
                  </div>
                </div>

                <div className="sm:text-right text-xs text-slate-500 space-y-0.5 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-200">
                  <p className="font-semibold text-slate-700">{backendResponse.standard_name}</p>
                  <p className="text-[11px] text-slate-600 max-w-xs">{backendResponse.standard_intended_use}</p>
                  <p className="text-[10px] font-mono text-slate-400">
                    Evaluated: {new Date(backendResponse.evaluated_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>

              {/* Reasons & Findings List */}
              {backendResponse.reasons && backendResponse.reasons.length > 0 && (
                <div className="mt-5 rounded-xl bg-white/80 p-4 border border-slate-200/80 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <Scale className="h-3.5 w-3.5 text-slate-500" />
                    <span>Evaluation Findings & Criteria Details:</span>
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-700">
                    {backendResponse.reasons.map((reason, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-slate-400 font-bold">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Boundary / Caution Warnings (if any) */}
              {backendResponse.warnings && backendResponse.warnings.length > 0 && (
                <div className="mt-3 rounded-xl bg-amber-100/70 p-3.5 border border-amber-300/80 text-xs text-amber-900 space-y-1">
                  <p className="font-bold flex items-center gap-1.5">
                    <AlertOctagon className="h-4 w-4 text-amber-700" />
                    <span>Threshold Boundary & Monitoring Notices:</span>
                  </p>
                  <ul className="list-disc pl-5 space-y-0.5 text-amber-800">
                    {backendResponse.warnings.map((warn, idx) => (
                      <li key={idx}>{warn}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Dedicated Machine Learning WQI Prediction Card */}
            {backendResponse.ml_prediction ? (
              <div className="rounded-2xl border-2 border-indigo-200 bg-gradient-to-br from-indigo-50/90 via-purple-50/50 to-white p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="mt-1 rounded-xl bg-indigo-600 p-2.5 text-white shadow-xs">
                      <Cpu className="h-7 w-7" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                          MACHINE LEARNING PREDICTION
                        </span>
                        <span className="text-[10px] font-bold uppercase rounded px-2 py-0.5 bg-indigo-100 text-indigo-800 border border-indigo-300">
                          {backendResponse.ml_prediction.algorithm || 'Decision Tree Regressor'}
                        </span>
                        <span className="text-[10px] font-bold uppercase rounded px-2 py-0.5 bg-emerald-100 text-emerald-800 border border-emerald-300">
                          ACTIVE MODEL
                        </span>
                      </div>
                      <div className="mt-2 flex items-baseline gap-3">
                        <span className="text-3xl font-black text-indigo-950">
                          {backendResponse.ml_prediction.wqi_score !== null && backendResponse.ml_prediction.wqi_score !== undefined
                            ? backendResponse.ml_prediction.wqi_score.toFixed(2)
                            : backendResponse.ml_prediction.prediction}
                        </span>
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                          Water Quality Index (WQI)
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-600 max-w-xl">
                        Calculated from all 12 chemical, physical, and biological parameters using the trained 
                        scikit-learn Decision Tree model (<code>{backendResponse.ml_prediction.model_version}</code>).
                      </p>
                    </div>
                  </div>

                  <div className="sm:text-right text-xs text-slate-500 border-t sm:border-t-0 pt-2 sm:pt-0 border-indigo-100 space-y-1">
                    <div className="inline-block rounded-lg bg-indigo-100/80 px-3 py-1.5 text-indigo-900 font-semibold">
                      Artifact: AquaWatchAI_Best_Model.joblib
                    </div>
                    <p className="text-[11px] text-slate-500">12 Features Processed</p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-indigo-100/80 flex items-start gap-2.5 text-xs text-slate-600">
                  <Info className="h-4 w-4 shrink-0 text-indigo-500 mt-0.5" />
                  <p className="text-[11px] leading-relaxed text-slate-600">
                    <strong className="text-slate-800">Scientific Distinction:</strong> {backendResponse.ml_prediction.disclaimer}
                  </p>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600 flex items-start gap-3">
                <Info className="h-5 w-5 shrink-0 text-slate-400 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-700">Machine Learning Status: {backendResponse.ml_model_status}</p>
                  <p className="text-slate-500 mt-0.5">{backendResponse.ml_model_details}</p>
                </div>
              </div>
            )}

            {/* Parameter-by-Parameter Assessment Table */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
                    Parameter-Wise Standard Assessment
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Comparison of submitted measurements against CPCB Class C & BIS IS 10500 baseline limits.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
                      <th className="py-2.5 px-3 font-semibold">Parameter</th>
                      <th className="py-2.5 px-3 font-semibold">Submitted Value</th>
                      <th className="py-2.5 px-3 font-semibold">Standard Baseline</th>
                      <th className="py-2.5 px-3 font-semibold">Assessment</th>
                      <th className="py-2.5 px-3 font-semibold">Criteria Findings</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {backendResponse.parameter_assessments.map((p, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-bold text-slate-900">
                          {p.display_name}
                        </td>
                        <td className="py-2.5 px-3 font-mono font-medium">
                          {p.value !== null && p.value !== undefined ? `${p.value} ${p.unit}` : <span className="text-slate-400 italic">Missing</span>}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-600">
                          {p.standard_range}
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold ${
                              p.status === 'PASS'
                                ? 'bg-emerald-100 text-emerald-800'
                                : p.status === 'FAIL'
                                ? 'bg-rose-100 text-rose-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-600 max-w-xs">
                          {p.message}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Scientific Limitations & Regulatory Disclaimer */}
            <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-3">
              <Info className="h-5 w-5 shrink-0 mt-0.5 text-blue-600" />
              <div className="space-y-1">
                <p className="font-bold text-blue-950">Scientific Limitations & Drinking Safety Disclaimer</p>
                <p className="text-blue-800 leading-relaxed">
                  {backendResponse.limitations}
                </p>
              </div>
            </div>

            {/* Inspector Toggle for Raw FastAPI Response JSON */}
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setShowRawJson(!showRawJson)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 underline"
              >
                <FileCode className="h-3.5 w-3.5" />
                <span>{showRawJson ? 'Hide' : 'Inspect'} Real FastAPI Response JSON</span>
              </button>

              {showRawJson && (
                <pre className="mt-2 rounded-lg bg-slate-900 p-4 text-[11px] font-mono text-emerald-400 overflow-x-auto">
                  {JSON.stringify(backendResponse, null, 2)}
                </pre>
              )}
            </div>

            {/* Post-Test Actions */}
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setBackendResponse(null)
                  if (activeSampleId === 'sample-a') handleLoadSample(DUMMY_SAMPLES[1])
                  else if (activeSampleId === 'sample-b') handleLoadSample(DUMMY_SAMPLES[2])
                  else handleLoadSample(DUMMY_SAMPLES[0])
                }}
                className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition-colors"
              >
                Test Next Predefined Sample
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="text-xs font-semibold text-slate-600 hover:underline"
              >
                Reset & Test Custom Sample
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
