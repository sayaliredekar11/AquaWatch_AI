import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
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
  Download,
  FileText,
  Search,
  Calendar,
  MapPin,
  Building2,
  UserCheck,
  Plus,
  X,
  History,
  Droplets,
  ExternalLink,
} from 'lucide-react'
import {
  testWaterQualityApi,
  getWaterBodiesApi,
  createWaterBodyApi,
  getWaterTestingReportsApi,
  getReportDownloadUrl,
} from '../services/api'
import { useAuth } from '../context/AuthContext'

// Helper to generate a unique Sample ID
function generateSampleId() {
  const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const rand = Math.random().toString(36).substring(2, 6).toUpperCase()
  return `SMP-${dateStr}-${rand}`
}

export default function TestWater() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const locationIdParam = searchParams.get('location_id')
  const { user } = useAuth()

  // Sample metadata
  const [sampleName, setSampleName] = useState('Laboratory Sample')
  const isDemo = false

  // 1. Sample Information
  const [sampleId, setSampleId] = useState(generateSampleId())
  const [sampleType, setSampleType] = useState('Surface Water')
  const [sampledAt, setSampledAt] = useState(new Date().toISOString().slice(0, 16))

  // Location selection
  const [waterBodies, setWaterBodies] = useState([])
  const [loadingBodies, setLoadingBodies] = useState(true)
  const [selectedWaterBodyId, setSelectedWaterBodyId] = useState('')

  // New location registration modal
  const [showNewLocationModal, setShowNewLocationModal] = useState(false)
  const [newLocName, setNewLocName] = useState('')
  const [newLocType, setNewLocType] = useState('river')
  const [newLocDesc, setNewLocDesc] = useState('')
  const [newLocDistrict, setNewLocDistrict] = useState('Sangli')
  const [newLocLat, setNewLocLat] = useState('')
  const [newLocLon, setNewLocLon] = useState('')
  const [creatingLocation, setCreatingLocation] = useState(false)
  const [locCreationError, setLocCreationError] = useState(null)

  // 2. Laboratory Information
  const [laboratoryName, setLaboratoryName] = useState(
    user?.laboratory_name || user?.laboratory?.name || 'Authorized Environmental Testing Laboratory'
  )
  const [labAuthorityName, setLabAuthorityName] = useState(user?.name || 'Authorized Lab Authority')
  const [testingDate, setTestingDate] = useState(new Date().toISOString().slice(0, 10))
  const [testingMethod, setTestingMethod] = useState('Standard Methods (APHA / IS 3025)')
  const [remarks, setRemarks] = useState('Sample collected under certified environmental protocols and tested within hold time.')

  // 3. All 14 Water Quality Parameters (initialized empty for genuine lab entry)
  // Core physical & chemical (CPCB / IS 10500 baseline)
  const [ph, setPh] = useState('')
  const [dissolvedOxygen, setDissolvedOxygen] = useState('')
  const [bod, setBod] = useState('')
  const [turbidity, setTurbidity] = useState('')
  const [tds, setTds] = useState('')

  // Chemical & Biological (ML model inputs)
  const [cod, setCod] = useState('')
  const [ammoniaN, setAmmoniaN] = useState('')
  const [chlorides, setChlorides] = useState('')
  const [sulphate, setSulphate] = useState('')
  const [phosphate, setPhosphate] = useState('')
  const [fecalColiform, setFecalColiform] = useState('')
  const [totalColiform, setTotalColiform] = useState('')

  // Secondary Physical Parameters
  const [electricalConductivity, setElectricalConductivity] = useState('')
  const [temperature, setTemperature] = useState('')
  const [nitrate, setNitrate] = useState('')

  // Submission and backend response states
  const [submitting, setSubmitting] = useState(false)
  const [clientError, setClientError] = useState(null)
  const [backendError, setBackendError] = useState(null)
  const [backendResponse, setBackendResponse] = useState(null)
  const [showRawJson, setShowRawJson] = useState(false)

  // Previous Reports state
  const [reports, setReports] = useState([])
  const [loadingReports, setLoadingReports] = useState(false)
  const [reportSearchQuery, setReportSearchQuery] = useState('')
  const [showPreviousReports, setShowPreviousReports] = useState(false)

  // Update lab authority name if user loads later
  useEffect(() => {
    if (user?.name && (!labAuthorityName || labAuthorityName === 'Authorized Lab Authority')) {
      setLabAuthorityName(user.name)
    }
  }, [user, labAuthorityName])

  // Load water bodies from PostgreSQL on mount
  useEffect(() => {
    setLoadingBodies(true)
    getWaterBodiesApi(0, 100)
      .then((bodies) => {
        setWaterBodies(bodies || [])
        if (bodies && bodies.length > 0) {
          if (locationIdParam) {
            const matched = bodies.find((b) => b.id.toString() === locationIdParam)
            if (matched) setSelectedWaterBodyId(matched.id.toString())
            else setSelectedWaterBodyId(bodies[0].id.toString())
          } else if (!selectedWaterBodyId) {
            setSelectedWaterBodyId(bodies[0].id.toString())
          }
        }
      })
      .catch((err) => {
        console.error('Failed to load water bodies:', err)
      })
      .finally(() => setLoadingBodies(false))
  }, [locationIdParam])

  // Load previous reports
  const fetchPreviousReports = async (query = '') => {
    setLoadingReports(true)
    try {
      const data = await getWaterTestingReportsApi({ search: query, limit: 15 })
      setReports(data?.items || [])
    } catch (err) {
      console.warn('Failed to load previous reports:', err.message)
    } finally {
      setLoadingReports(false)
    }
  }

  useEffect(() => {
    fetchPreviousReports()
  }, [])

  // Selected water body object
  const selectedWaterBody = waterBodies.find(
    (b) => b.id.toString() === selectedWaterBodyId
  )

  // Reset form to blank state
  const handleReset = () => {
    setSampleName('Laboratory Sample')
    setSampleId(generateSampleId())
    setPh('')
    setDissolvedOxygen('')
    setBod('')
    setTurbidity('')
    setTds('')
    setCod('')
    setAmmoniaN('')
    setChlorides('')
    setSulphate('')
    setPhosphate('')
    setFecalColiform('')
    setTotalColiform('')
    setElectricalConductivity('')
    setTemperature('')
    setNitrate('')
    setClientError(null)
    setBackendError(null)
    setBackendResponse(null)
    setShowRawJson(false)
  }

  // Submit new location modal
  const handleCreateNewLocation = async (e) => {
    e.preventDefault()
    setLocCreationError(null)
    if (!newLocName || !newLocDesc) {
      setLocCreationError('Location name and description are required.')
      return
    }

    setCreatingLocation(true)
    try {
      const payload = {
        name: newLocName.trim(),
        water_body_type: newLocType,
        location_name: newLocDesc.trim(),
        district: newLocDistrict.trim() || 'Maharashtra',
        state: 'Maharashtra',
        latitude: newLocLat ? parseFloat(newLocLat) : 16.85,
        longitude: newLocLon ? parseFloat(newLocLon) : 74.58,
      }
      const created = await createWaterBodyApi(payload)
      setWaterBodies((prev) => [created, ...prev])
      setSelectedWaterBodyId(created.id.toString())
      setShowNewLocationModal(false)
      setNewLocName('')
      setNewLocDesc('')
      setNewLocLat('')
      setNewLocLon('')
    } catch (err) {
      setLocCreationError(err.message || 'Failed to register new monitoring location.')
    } finally {
      setCreatingLocation(false)
    }
  }

  // Submit measurements to real FastAPI backend
  const handleSubmit = async (e) => {
    e.preventDefault()
    setClientError(null)
    setBackendError(null)
    setBackendResponse(null)

    if (!selectedWaterBodyId) {
      setClientError('A monitored water body location is required. Please select a monitoring location.')
      return
    }

    // Build payload with null for empty fields
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
    const parsedPhosphate = phosphate !== '' && !isNaN(parseFloat(phosphate)) ? parseFloat(phosphate) : null
    const parsedFecal = fecalColiform !== '' && !isNaN(parseFloat(fecalColiform)) ? parseFloat(fecalColiform) : null
    const parsedTotal = totalColiform !== '' && !isNaN(parseFloat(totalColiform)) ? parseFloat(totalColiform) : null

    // Secondary
    const parsedEc = electricalConductivity !== '' && !isNaN(parseFloat(electricalConductivity)) ? parseFloat(electricalConductivity) : null
    const parsedTemp = temperature !== '' && !isNaN(parseFloat(temperature)) ? parseFloat(temperature) : null
    const parsedNitrate = nitrate !== '' && !isNaN(parseFloat(nitrate)) ? parseFloat(nitrate) : null

    const payload = {
      sample_name: sampleName || 'Lab Sample',
      sample_id: sampleId || generateSampleId(),
      sample_type: sampleType,
      laboratory_name: laboratoryName,
      lab_authority_name: labAuthorityName,
      testing_date: testingDate ? new Date(testingDate).toISOString() : null,
      sampled_at: sampledAt ? new Date(sampledAt).toISOString() : null,
      testing_method: testingMethod,
      remarks: remarks,
      is_demo: isDemo,
      location_id: parseInt(selectedWaterBodyId, 10),
      water_body_id: parseInt(selectedWaterBodyId, 10),
      save_to_db: true,
      ph: parsedPh,
      dissolved_oxygen: parsedDo,
      bod: parsedBod,
      turbidity: parsedTurbidity,
      tds: parsedTds,
      cod: parsedCod,
      ammonia_n: parsedAmmonia,
      chlorides: parsedChlorides,
      sulphate: parsedSulphate,
      phosphate: parsedPhosphate,
      fecal_coliform: parsedFecal,
      total_coliform: parsedTotal,
      electrical_conductivity: parsedEc,
      temperature: parsedTemp,
      nitrate: parsedNitrate,
    }

    setSubmitting(true)
    try {
      const result = await testWaterQualityApi(payload)
      setBackendResponse(result)
      // Refresh previous reports list
      fetchPreviousReports()
    } catch (err) {
      setBackendError(err.message || 'Failed to communicate with FastAPI backend server.')
    } finally {
      setSubmitting(false)
    }
  }

  // Handle PDF Download
  const handleDownloadPdf = (reportId) => {
    if (!reportId) return
    const url = getReportDownloadUrl(reportId)
    window.open(url, '_blank')
  }

  return (
    <div className="min-h-[calc(100vh-65px)] bg-slate-50 px-4 py-8 sm:px-6 lg:px-8 animate-fade-in">
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-md bg-blue-100 px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-blue-800">
                LAB_AUTHORITY ACCESS
              </span>
              <span className="inline-flex items-center rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                14-PARAMETER TESTING + ML WQI
              </span>
              <span className="inline-flex items-center rounded-md bg-purple-100 px-2 py-0.5 text-xs font-semibold text-purple-800">
                A4 PDF CERTIFIED
              </span>
            </div>
            <h1 className="mt-2 text-2xl font-black text-slate-900 sm:text-3xl flex items-center gap-2.5">
              <FlaskConical className="h-7 w-7 text-blue-600" />
              <span>Water Testing & Certified PDF Report Generation</span>
            </h1>
            <p className="mt-1 text-sm text-slate-600 max-w-3xl">
              Conduct official 14-parameter laboratory testing for monitored Maharashtra water bodies. Evaluates CPCB / IS 10500 baseline safety, calculates ML Water Quality Index (WQI), persists historical records, and generates downloadable official PDF reports.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setShowPreviousReports(!showPreviousReports)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
            >
              <History className="h-4 w-4 text-slate-500" />
              <span>{showPreviousReports ? 'Hide Reports' : 'Previous Reports'}</span>
            </button>
          </div>
        </div>

        {/* Section 1: Laboratory Testing Form */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-8 shadow-xs space-y-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
                  Laboratory Testing & Sample Information
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Associates the test record with a monitoring location and records laboratory audit metadata.
                </p>
              </div>
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900 underline"
              >
                <RotateCcw className="h-3 w-3" />
                <span>Clear Form</span>
              </button>
            </div>

            {/* Geographical Monitoring Location Dropdown (REQUIRED) */}
            <div className="rounded-xl border-2 border-blue-100 bg-blue-50/40 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-blue-600" />
                  <label className="text-xs font-bold uppercase tracking-wider text-blue-900">
                    Geographical Monitoring Location *
                  </label>
                </div>
                <button
                  type="button"
                  onClick={() => setShowNewLocationModal(true)}
                  className="inline-flex items-center gap-1 rounded bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-xs"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Register New Location</span>
                </button>
              </div>

              {loadingBodies ? (
                <div className="h-10 animate-pulse rounded-lg bg-slate-200" />
              ) : (
                <select
                  value={selectedWaterBodyId}
                  onChange={(e) => setSelectedWaterBodyId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 font-semibold focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  required
                >
                  <option value="">-- Select Monitored Water Body / Location --</option>
                  {waterBodies.map((wb) => (
                    <option key={wb.id} value={wb.id}>
                      {wb.name} — {wb.location_name} ({wb.district || 'Maharashtra'}) [ID: #{wb.id}]
                    </option>
                  ))}
                </select>
              )}

              {selectedWaterBody && (
                <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-600">
                  <span className="inline-flex items-center gap-1 bg-white px-2 py-0.5 rounded border border-slate-200 font-medium">
                    <Droplets className="h-3.5 w-3.5 text-cyan-600" />
                    <span className="capitalize">{selectedWaterBody.water_body_type}</span>
                  </span>
                  <span className="inline-flex items-center gap-1 bg-white px-2 py-0.5 rounded border border-slate-200">
                    <MapPin className="h-3.5 w-3.5 text-rose-500" />
                    <span>{selectedWaterBody.district || 'Maharashtra'}, {selectedWaterBody.state || 'Maharashtra'}</span>
                  </span>
                  {selectedWaterBody.latitude && selectedWaterBody.longitude && (
                    <span className="font-mono text-slate-500">
                      GPS: {selectedWaterBody.latitude.toFixed(4)}°N, {selectedWaterBody.longitude.toFixed(4)}°E
                    </span>
                  )}
                  <Link
                    to={`/intelligence?location_id=${selectedWaterBody.id}`}
                    className="ml-auto inline-flex items-center gap-1 text-blue-600 hover:underline font-semibold"
                  >
                    <span>View Location History</span>
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
              )}
            </div>

            {/* Sample Information Card */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-slate-500" />
                <span>Sample Details & Identification</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Sample ID (Auto-Generated)
                  </label>
                  <div className="flex gap-1.5">
                    <input
                      type="text"
                      value={sampleId}
                      onChange={(e) => setSampleId(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-mono font-bold text-slate-800"
                      placeholder="SMP-20261104-XXXX"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setSampleId(generateSampleId())}
                      className="rounded border border-slate-300 bg-white p-2 text-slate-500 hover:bg-slate-100"
                      title="Generate new Sample ID"
                    >
                      <RotateCcw className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Sample Name / Label
                  </label>
                  <input
                    type="text"
                    value={sampleName}
                    onChange={(e) => setSampleName(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
                    placeholder="e.g. Krishna Ghat Station A"
                    required
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Sample Type
                  </label>
                  <select
                    value={sampleType}
                    onChange={(e) => setSampleType(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800"
                  >
                    <option value="Surface Water">Surface Water (River / Stream)</option>
                    <option value="Lake / Reservoir">Lake / Reservoir</option>
                    <option value="Groundwater">Groundwater (Borewell / Well)</option>
                    <option value="Drinking Water">Municipal Drinking Water Supply</option>
                    <option value="Treated Wastewater">Treated Effluent / STP Output</option>
                    <option value="Industrial Effluent">Industrial Effluent (Screening)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Collection Date & Time
                  </label>
                  <input
                    type="datetime-local"
                    value={sampledAt}
                    onChange={(e) => setSampledAt(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>
              </div>
            </div>

            {/* Laboratory & Technician Information Card */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-slate-500" />
                <span>Testing Laboratory & Analyst Information</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Laboratory Name
                  </label>
                  <input
                    type="text"
                    value={laboratoryName}
                    onChange={(e) => setLaboratoryName(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Lab Authority / Technician
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={labAuthorityName}
                      onChange={(e) => setLabAuthorityName(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-800"
                    />
                    <UserCheck className="absolute right-2.5 top-2.5 h-3.5 w-3.5 text-emerald-600" />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Testing Date
                  </label>
                  <input
                    type="date"
                    value={testingDate}
                    onChange={(e) => setTestingDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Testing Method
                  </label>
                  <input
                    type="text"
                    value={testingMethod}
                    onChange={(e) => setTestingMethod(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800"
                    placeholder="e.g. APHA / IS 3025"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 mb-1 block">
                  Remarks / Analytical Field Notes (Optional)
                </label>
                <input
                  type="text"
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800"
                  placeholder="Notes regarding sample preservation, clarity, weather, or holding time..."
                />
              </div>
            </div>

            {/* Core 14 Parameters Section */}
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                    <Sparkles className="h-4 w-4 text-ocean" />
                    <span>14 Water Quality Parameters</span>
                  </h3>
                  <p className="text-xs text-slate-500">
                    All 14 parameters will be evaluated and printed on the official A4 PDF report.
                  </p>
                </div>
                <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-200">
                  Includes 12 Model Features for WQI
                </span>
              </div>

              {/* Group 1: Core Physical Parameters */}
              <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
                  Group A: Core Physical & Basic Screening Parameters
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
                  {/* 1. pH */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      1. pH (Std: 6.5 – 8.5)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={ph}
                      onChange={(e) => setPh(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-semibold focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="e.g. 7.2"
                    />
                    <span className="text-[10px] text-slate-400 mt-0.5 block">Standard units</span>
                  </div>

                  {/* 2. Dissolved Oxygen */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      2. DO (Std: ≥ 4.0 mg/L)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={dissolvedOxygen}
                      onChange={(e) => setDissolvedOxygen(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-semibold focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="e.g. 7.0"
                    />
                    <span className="text-[10px] text-slate-400 mt-0.5 block">Dissolved Oxygen</span>
                  </div>

                  {/* 3. BOD */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      3. BOD (Std: ≤ 3.0 mg/L)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={bod}
                      onChange={(e) => setBod(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-semibold focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="e.g. 2.0"
                    />
                    <span className="text-[10px] text-slate-400 mt-0.5 block">Biochemical O₂</span>
                  </div>

                  {/* 4. Turbidity */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      4. Turbidity (≤ 5.0 NTU)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={turbidity}
                      onChange={(e) => setTurbidity(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-semibold focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="e.g. 3.0"
                    />
                    <span className="text-[10px] text-slate-400 mt-0.5 block">Clarity Index (NTU)</span>
                  </div>

                  {/* 5. TDS */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      5. TDS (≤ 500 mg/L)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={tds}
                      onChange={(e) => setTds(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 font-semibold focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="e.g. 250"
                    />
                    <span className="text-[10px] text-slate-400 mt-0.5 block">Total Dissolved Solids</span>
                  </div>
                </div>
              </div>

              {/* Group 2: Advanced Chemical & Biological Parameters (ML Model Features + Phosphate) */}
              <div className="rounded-xl border border-indigo-200 bg-indigo-50/40 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Cpu className="h-4 w-4 text-indigo-600" />
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-950">
                      Group B: Chemical & Biological Parameters (ML Model + Laboratory Nutrients)
                    </span>
                  </div>
                  <span className="text-[10px] font-bold text-indigo-800 bg-indigo-100 px-2 py-0.5 rounded">
                    DecisionTreeRegressor Inputs
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                  {/* 6. COD */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      6. COD (mg/L, Chemical Oxygen Demand)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={cod}
                      onChange={(e) => setCod(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-semibold focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g. 10.0"
                    />
                  </div>

                  {/* 7. Ammonia Nitrogen */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      7. Ammonia Nitrogen (mg/L, Amonia N)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={ammoniaN}
                      onChange={(e) => setAmmoniaN(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-semibold focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g. 0.2"
                    />
                  </div>

                  {/* 8. Chlorides */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      8. Chloride / Chlorides (mg/L)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={chlorides}
                      onChange={(e) => setChlorides(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-semibold focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g. 25.0"
                    />
                  </div>

                  {/* 9. Sulphate */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      9. Sulphate (mg/L)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={sulphate}
                      onChange={(e) => setSulphate(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-semibold focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g. 30.0"
                    />
                  </div>

                  {/* 10. Phosphate (NEW) */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block flex items-center justify-between">
                      <span>10. Phosphate (mg/L)</span>
                      <span className="text-[10px] text-indigo-600 font-bold bg-indigo-50 px-1.5 py-0.2 rounded border border-indigo-200">New</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={phosphate}
                      onChange={(e) => setPhosphate(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-semibold focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g. 0.05"
                    />
                  </div>

                  {/* 11. Total Coliform */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      11. Total Coliform (MPN/100 mL)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={totalColiform}
                      onChange={(e) => setTotalColiform(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-semibold focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g. 50.0"
                    />
                  </div>

                  {/* 12. Fecal Coliform */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      12. Fecal Coliform (MPN/100 mL)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={fecalColiform}
                      onChange={(e) => setFecalColiform(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 font-semibold focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      placeholder="e.g. 20.0"
                    />
                  </div>
                </div>
              </div>

              {/* Group 3: Secondary Physical & Environmental Parameters */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
                  Group C: Secondary Electrical & Environmental Parameters
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                  {/* 13. Electrical Conductivity */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      13. Electrical Cond. (EC, µS/cm)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={electricalConductivity}
                      onChange={(e) => setElectricalConductivity(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
                      placeholder="e.g. 320"
                    />
                  </div>

                  {/* 14. Temperature */}
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      14. Water Temperature (°C)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
                      placeholder="e.g. 22.0"
                    />
                  </div>

                  {/* Nitrate */}
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
                      placeholder="e.g. 1.2"
                    />
                  </div>
                </div>
              </div>
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
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 transition-colors cursor-pointer"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Evaluating & Generating Certified PDF...</span>
                  </>
                ) : (
                  <>
                    <FlaskConical className="h-4 w-4" />
                    <span>Submit & Generate Certified PDF Report</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Section 3: Prominent Safety Classification Banner & Findings */}
        {backendResponse && (
          <div className="space-y-6 animate-fade-slide-up">
            {/* Classification & PDF Action Card */}
            <div
              className={`rounded-2xl border-2 p-6 shadow-sm transition-all ${
                backendResponse.classification === 'SAFE'
                  ? 'border-emerald-400 bg-emerald-50/90'
                  : backendResponse.classification === 'HARMFUL'
                  ? 'border-rose-400 bg-rose-50/90'
                  : 'border-amber-400 bg-amber-50/90'
              }`}
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
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
                    <div className="mt-1 flex flex-wrap items-center gap-3">
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
                        Sample ID: <strong className="font-mono text-blue-700">{backendResponse.sample_id}</strong>
                      </span>
                      <span className="text-xs text-slate-500">
                        Report ID: <strong className="font-mono text-slate-700">{backendResponse.report_id}</strong>
                      </span>
                    </div>
                    <p className="mt-1.5 text-xs text-slate-700 leading-relaxed">
                      {backendResponse.message}
                    </p>
                  </div>
                </div>

                {/* PDF Download Button */}
                <div className="flex flex-col sm:flex-row lg:flex-col gap-2 shrink-0 pt-2 lg:pt-0">
                  <button
                    type="button"
                    onClick={() => handleDownloadPdf(backendResponse.report_id)}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-700 hover:bg-blue-800 px-5 py-3 text-sm font-bold text-white shadow-md transition-all active:scale-[0.98] cursor-pointer"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download Official PDF Report</span>
                  </button>
                  <p className="text-[11px] text-center text-slate-500">
                    A4 PDF generated & persisted in database
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
                        {backendResponse.wqi_category && (
                          <span className="rounded-full bg-indigo-600 text-white px-3 py-0.5 text-xs font-bold shadow-xs">
                            {backendResponse.wqi_category}
                          </span>
                        )}
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
                    <p className="text-[11px] text-slate-500">12 Features Processed &middot; WQI Computed</p>
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

            {/* Post-Test Actions */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => handleDownloadPdf(backendResponse.report_id)}
                className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition-colors shadow-xs"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download Report ({backendResponse.report_id})</span>
              </button>
              <Link
                to={`/intelligence?location_id=${backendResponse.location_id || backendResponse.water_body_id}`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <Activity className="h-3.5 w-3.5 text-blue-600" />
                <span>View Historical Trends for this Location</span>
              </Link>
              <button
                type="button"
                onClick={handleReset}
                className="text-xs font-semibold text-slate-600 hover:underline"
              >
                Test Another Sample
              </button>
            </div>
          </div>
        )}

        {/* Section 4: Previous Water Testing Reports (Requirement 6) */}
        {showPreviousReports && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
                  <History className="h-4 w-4 text-blue-600" />
                  <span>Previous Laboratory Water Testing Reports</span>
                </h3>
                <p className="text-xs text-slate-500">
                  Search, review, and download certified PDF reports from historical tests.
                </p>
              </div>

              {/* Search Bar */}
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="text"
                    value={reportSearchQuery}
                    onChange={(e) => {
                      setReportSearchQuery(e.target.value)
                      fetchPreviousReports(e.target.value)
                    }}
                    placeholder="Search Sample ID or Report ID..."
                    className="w-56 sm:w-64 rounded-lg border border-slate-300 py-1.5 pl-8 pr-3 text-xs text-slate-800 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {loadingReports ? (
              <div className="py-8 text-center text-xs text-slate-500">
                <Loader2 className="h-5 w-5 animate-spin text-blue-600 mx-auto mb-1" />
                <span>Loading report archive...</span>
              </div>
            ) : reports.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500 space-y-1">
                <FileText className="h-6 w-6 text-slate-400 mx-auto" />
                <p className="font-semibold text-slate-700">No testing reports found</p>
                <p className="text-slate-400">Newly submitted test samples will automatically generate reports here.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold">
                      <th className="py-2 px-3">Date</th>
                      <th className="py-2 px-3">Sample ID</th>
                      <th className="py-2 px-3">Report ID</th>
                      <th className="py-2 px-3">Water Body</th>
                      <th className="py-2 px-3">WQI Score</th>
                      <th className="py-2 px-3">Category</th>
                      <th className="py-2 px-3">Status</th>
                      <th className="py-2 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {reports.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/70">
                        <td className="py-2.5 px-3 font-medium text-slate-500">
                          {new Date(r.measured_at).toLocaleDateString('en-GB', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </td>
                        <td className="py-2.5 px-3 font-mono font-bold text-blue-700">
                          {r.sample_id}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-600">
                          {r.report_id}
                        </td>
                        <td className="py-2.5 px-3 font-semibold text-slate-900">
                          {r.water_body_name || 'Water Body'} ({r.district || 'MH'})
                        </td>
                        <td className="py-2.5 px-3 font-mono font-bold text-indigo-900">
                          {r.wqi_score !== null && r.wqi_score !== undefined ? r.wqi_score.toFixed(2) : '—'}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="text-[10px] font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                            {r.wqi_category || '—'}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                              r.safety_classification === 'SAFE'
                                ? 'bg-emerald-100 text-emerald-800'
                                : r.safety_classification === 'HARMFUL'
                                ? 'bg-rose-100 text-rose-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            {r.safety_classification || 'EVALUATED'}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            type="button"
                            onClick={() => handleDownloadPdf(r.report_id || r.id)}
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 underline cursor-pointer"
                          >
                            <Download className="h-3 w-3" />
                            <span>Download PDF</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Modal: Register New Location */}
        {showNewLocationModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2 text-slate-900">
                  <MapPin className="h-5 w-5 text-blue-600" />
                  <h3 className="font-bold text-base">Register Monitored Water Body</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setShowNewLocationModal(false)}
                  className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {locCreationError && (
                <div className="rounded-lg bg-rose-50 p-3 text-xs text-rose-700 border border-rose-200">
                  {locCreationError}
                </div>
              )}

              <form onSubmit={handleCreateNewLocation} className="space-y-3.5">
                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Water Body Name *
                  </label>
                  <input
                    type="text"
                    value={newLocName}
                    onChange={(e) => setNewLocName(e.target.value)}
                    placeholder="e.g. Panchganga River"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs text-slate-800"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      Type *
                    </label>
                    <select
                      value={newLocType}
                      onChange={(e) => setNewLocType(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs text-slate-800"
                    >
                      <option value="river">River</option>
                      <option value="lake">Lake</option>
                      <option value="reservoir">Reservoir</option>
                      <option value="canal">Canal</option>
                      <option value="stream">Stream</option>
                      <option value="well">Well</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      District *
                    </label>
                    <input
                      type="text"
                      value={newLocDistrict}
                      onChange={(e) => setNewLocDistrict(e.target.value)}
                      placeholder="e.g. Kolhapur"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs text-slate-800"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 mb-1 block">
                    Location Description *
                  </label>
                  <input
                    type="text"
                    value={newLocDesc}
                    onChange={(e) => setNewLocDesc(e.target.value)}
                    placeholder="e.g. Shiroli Basin, Kolhapur"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs text-slate-800"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      Latitude
                    </label>
                    <input
                      type="number"
                      step="0.0001"
                      value={newLocLat}
                      onChange={(e) => setNewLocLat(e.target.value)}
                      placeholder="e.g. 16.7128"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs text-slate-800"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-700 mb-1 block">
                      Longitude
                    </label>
                    <input
                      type="number"
                      step="0.0001"
                      value={newLocLon}
                      onChange={(e) => setNewLocLon(e.target.value)}
                      placeholder="e.g. 74.2384"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs text-slate-800"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setShowNewLocationModal(false)}
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creatingLocation}
                    className="rounded-lg bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {creatingLocation ? 'Saving...' : 'Register Location'}
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
