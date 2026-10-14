import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FlaskConical,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Calendar,
  MapPin,
  FileText,
  Loader2,
  Info,
} from 'lucide-react'
import {
  getWaterBodiesApi,
  createWaterBodyApi,
  createWaterQualityRecordApi,
  predictWaterQualityApi,
} from '../services/api'

export default function TestWater() {
  const navigate = useNavigate()

  const [waterBodies, setWaterBodies] = useState([])
  const [loadingBodies, setLoadingBodies] = useState(true)

  // Quick inline creation state if no water body exists
  const [showNewWbModal, setShowNewWbModal] = useState(false)
  const [newWbName, setNewWbName] = useState('')
  const [newWbType, setNewWbType] = useState('river')
  const [newWbLocation, setNewWbLocation] = useState('')
  const [newWbLat, setNewWbLat] = useState('')
  const [newWbLng, setNewWbLng] = useState('')

  // Form state
  const [selectedWaterBodyId, setSelectedWaterBodyId] = useState('')
  const [measuredAt, setMeasuredAt] = useState(
    new Date().toISOString().slice(0, 16)
  )

  const [ph, setPh] = useState('7.4')
  const [dissolvedOxygen, setDissolvedOxygen] = useState('6.8')
  const [bod, setBod] = useState('2.1')
  const [turbidity, setTurbidity] = useState('4.2')
  const [tds, setTds] = useState('240')
  const [electricalConductivity, setElectricalConductivity] = useState('350')
  const [nitrate, setNitrate] = useState('1.5')
  const [temperature, setTemperature] = useState('24.0')

  // Status & response
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [successRecord, setSuccessRecord] = useState(null)
  const [predictionResult, setPredictionResult] = useState(null)
  const [predicting, setPredicting] = useState(false)

  // Load water bodies from backend
  const loadWaterBodies = async () => {
    setLoadingBodies(true)
    try {
      const bodies = await getWaterBodiesApi(0, 100)
      setWaterBodies(bodies || [])
      if (bodies && bodies.length > 0 && !selectedWaterBodyId) {
        setSelectedWaterBodyId(bodies[0].id.toString())
      }
    } catch (err) {
      console.error('Failed to load water bodies:', err)
    } finally {
      setLoadingBodies(false)
    }
  }

  useEffect(() => {
    loadWaterBodies()
  }, [])

  const handleCreateWaterBody = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const created = await createWaterBodyApi({
        name: newWbName.trim(),
        water_body_type: newWbType,
        location_name: newWbLocation.trim(),
        latitude: newWbLat ? parseFloat(newWbLat) : null,
        longitude: newWbLng ? parseFloat(newWbLng) : null,
      })
      setShowNewWbModal(false)
      await loadWaterBodies()
      setSelectedWaterBodyId(created.id.toString())
    } catch (err) {
      setError(`Failed to create water body: ${err.message}`)
    }
  }

  const handleReset = () => {
    setPh('7.4')
    setDissolvedOxygen('6.8')
    setBod('2.1')
    setTurbidity('4.2')
    setTds('240')
    setElectricalConductivity('350')
    setNitrate('1.5')
    setTemperature('24.0')
    setError(null)
    setSuccessRecord(null)
    setPredictionResult(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccessRecord(null)
    setPredictionResult(null)

    if (!selectedWaterBodyId) {
      setError('Please select or create a monitored water body first.')
      return
    }

    // Client-side numeric validation
    const phVal = parseFloat(ph)
    if (isNaN(phVal) || phVal < 0 || phVal > 14) {
      setError('pH must be a valid number between 0.0 and 14.0.')
      return
    }

    const doVal = parseFloat(dissolvedOxygen)
    if (isNaN(doVal) || doVal < 0) {
      setError('Dissolved Oxygen must be non-negative (>= 0.0 mg/L).')
      return
    }

    const payload = {
      water_body_id: parseInt(selectedWaterBodyId, 10),
      measured_at: new Date(measuredAt).toISOString(),
      ph: phVal,
      dissolved_oxygen: doVal,
      bod: bod ? parseFloat(bod) : null,
      turbidity: turbidity ? parseFloat(turbidity) : null,
      tds: tds ? parseFloat(tds) : null,
      electrical_conductivity: electricalConductivity
        ? parseFloat(electricalConductivity)
        : null,
      nitrate: nitrate ? parseFloat(nitrate) : null,
      temperature: temperature ? parseFloat(temperature) : null,
    }

    setSubmitting(true)

    try {
      // 1. Submit measurement record to POST /water-quality
      const saved = await createWaterQualityRecordApi(payload)
      setSuccessRecord(saved)

      // 2. Optional: check ML inference if features meet requirements
      setPredicting(true)
      try {
        const pred = await predictWaterQualityApi({
          ph: payload.ph,
          dissolved_oxygen: payload.dissolved_oxygen,
          bod: payload.bod ?? 2.0,
          turbidity: payload.turbidity ?? 5.0,
          tds: payload.tds ?? 250.0,
          electrical_conductivity: payload.electrical_conductivity,
          nitrate: payload.nitrate,
          temperature: payload.temperature,
        })
        setPredictionResult({ available: true, data: pred })
      } catch (predErr) {
        setPredictionResult({
          available: false,
          status: predErr.status,
          message:
            predErr.status === 503
              ? 'ML model integration pending deployment from ML teammate.'
              : predErr.message,
        })
      } finally {
        setPredicting(false)
      }
    } catch (err) {
      setError(err.message || 'Failed to submit water quality record to backend.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-65px)] bg-mist px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Header */}
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-ocean">
            LABORATORY ENTRY
          </span>
          <h1 className="mt-1 text-2xl font-extrabold text-ink sm:text-3xl flex items-center gap-2">
            <FlaskConical className="h-7 w-7 text-ocean" />
            <span>Record Water Quality Sample</span>
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Log standardized chemical & physical measurements into the PostgreSQL database.
          </p>
        </div>

        {/* Schema Scope Notice */}
        <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-3">
          <Info className="h-5 w-5 shrink-0 mt-0.5 text-blue-600" />
          <div className="space-y-1">
            <p className="font-semibold text-blue-950">Backend Parameter Mapping Notice</p>
            <p className="text-blue-800">
              The backend tracks standard water quality parameters: <strong>pH, Dissolved Oxygen, BOD, Turbidity, TDS, Electrical Conductivity, Nitrate, and Temperature</strong>.
              Prototype parameters COD and Phosphate are reserved for future lab expansions.
            </p>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5 text-rose-600" />
            <div className="flex-1">
              <p className="font-semibold">Submission Error</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Success Confirmation Alert */}
        {successRecord && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-900 space-y-3">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-6 w-6 shrink-0 text-emerald-600" />
              <div className="flex-1">
                <p className="font-bold text-base text-emerald-950">
                  Record #{successRecord.id} Successfully Saved to PostgreSQL
                </p>
                <p className="text-xs text-emerald-800 mt-1">
                  Water quality measurement has been securely saved and linked to Water Body ID #{successRecord.water_body_id}.
                </p>
              </div>
            </div>

            {/* Prediction status section */}
            {predictionResult && (
              <div className="rounded-lg border border-emerald-300 bg-white/80 p-3 text-xs space-y-1">
                <p className="font-semibold text-slate-800 flex items-center gap-1.5">
                  <Sparkles className="h-4 w-4 text-ocean" />
                  <span>Machine Learning Prediction Status:</span>
                </p>
                {predictionResult.available ? (
                  <p className="text-slate-700">
                    Classification: <strong>{predictionResult.data.prediction}</strong> (Confidence: {(predictionResult.data.confidence * 100).toFixed(1)}%)
                  </p>
                ) : (
                  <p className="text-slate-600 italic">
                    {predictionResult.message}
                  </p>
                )}
              </div>
            )}

            <div className="flex items-center gap-3 pt-1">
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="rounded-lg bg-emerald-700 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-800 transition-colors"
              >
                View in Dashboard
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="text-xs font-semibold text-emerald-800 hover:underline"
              >
                Log Another Sample
              </button>
            </div>
          </div>
        )}

        {/* Form Card */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-xs space-y-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Station Selection */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                  Monitored Water Body
                </label>
                {loadingBodies ? (
                  <div className="h-10 animate-pulse rounded-lg bg-slate-100" />
                ) : (
                  <div className="flex gap-2">
                    <select
                      value={selectedWaterBodyId}
                      onChange={(e) => setSelectedWaterBodyId(e.target.value)}
                      className="input text-sm text-slate-800 font-medium flex-1"
                      required
                    >
                      <option value="">-- Select Water Body --</option>
                      {waterBodies.map((wb) => (
                        <option key={wb.id} value={wb.id}>
                          {wb.name} ({wb.location_name})
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => setShowNewWbModal(true)}
                      className="rounded-lg border border-slate-300 px-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                      title="Add New Water Body"
                    >
                      + New
                    </button>
                  </div>
                )}
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 mb-1.5 block">
                  Sampling Timestamp
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="datetime-local"
                    value={measuredAt}
                    onChange={(e) => setMeasuredAt(e.target.value)}
                    required
                    className="input pl-9 text-slate-800 text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Measurement Parameters Grid */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Laboratory Parameter Values
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    pH (0.0 – 14.0) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="14"
                    value={ph}
                    onChange={(e) => setPh(e.target.value)}
                    required
                    className="input text-sm text-slate-800"
                    placeholder="7.4"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Dissolved Oxygen (mg/L) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={dissolvedOxygen}
                    onChange={(e) => setDissolvedOxygen(e.target.value)}
                    required
                    className="input text-sm text-slate-800"
                    placeholder="6.8"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    BOD (mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={bod}
                    onChange={(e) => setBod(e.target.value)}
                    className="input text-sm text-slate-800"
                    placeholder="2.1"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Turbidity (NTU)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={turbidity}
                    onChange={(e) => setTurbidity(e.target.value)}
                    className="input text-sm text-slate-800"
                    placeholder="4.2"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    TDS (mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={tds}
                    onChange={(e) => setTds(e.target.value)}
                    className="input text-sm text-slate-800"
                    placeholder="240"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Conductivity (µS/cm)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={electricalConductivity}
                    onChange={(e) => setElectricalConductivity(e.target.value)}
                    className="input text-sm text-slate-800"
                    placeholder="350"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Nitrate (mg/L)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={nitrate}
                    onChange={(e) => setNitrate(e.target.value)}
                    className="input text-sm text-slate-800"
                    placeholder="1.5"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Temperature (°C)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="-20"
                    max="100"
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    className="input text-sm text-slate-800"
                    placeholder="24.0"
                  />
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset Form</span>
              </button>

              <button
                type="submit"
                disabled={submitting}
                className="btn-primary font-semibold flex items-center gap-2 py-2.5 px-6 shadow-sm disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Saving to Database...</span>
                  </>
                ) : (
                  <>
                    <FlaskConical className="h-4 w-4" />
                    <span>Save Laboratory Record</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Modal to add a new water body */}
        {showNewWbModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
            <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg space-y-4">
              <h3 className="font-bold text-lg text-ink">Add Monitored Water Body</h3>
              <form onSubmit={handleCreateWaterBody} className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={newWbName}
                    onChange={(e) => setNewWbName(e.target.value)}
                    className="input text-sm text-slate-800"
                    placeholder="e.g. Krishna River"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Type *
                  </label>
                  <select
                    value={newWbType}
                    onChange={(e) => setNewWbType(e.target.value)}
                    className="input text-sm text-slate-800 font-medium"
                  >
                    <option value="river">River</option>
                    <option value="lake">Lake</option>
                    <option value="reservoir">Reservoir</option>
                    <option value="canal">Canal</option>
                    <option value="stream">Stream</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Location Description *
                  </label>
                  <input
                    type="text"
                    required
                    value={newWbLocation}
                    onChange={(e) => setNewWbLocation(e.target.value)}
                    className="input text-sm text-slate-800"
                    placeholder="e.g. Sangli Ghat"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 block mb-1">
                      Latitude
                    </label>
                    <input
                      type="number"
                      step="0.0001"
                      value={newWbLat}
                      onChange={(e) => setNewWbLat(e.target.value)}
                      className="input text-sm text-slate-800"
                      placeholder="16.8524"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-700 block mb-1">
                      Longitude
                    </label>
                    <input
                      type="number"
                      step="0.0001"
                      value={newWbLng}
                      onChange={(e) => setNewWbLng(e.target.value)}
                      className="input text-sm text-slate-800"
                      placeholder="74.5815"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-3">
                  <button
                    type="button"
                    onClick={() => setShowNewWbModal(false)}
                    className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary text-xs font-semibold py-2 px-4"
                  >
                    Create Station
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
