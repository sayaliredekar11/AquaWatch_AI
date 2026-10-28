import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from 'recharts'
import {
  Activity,
  AlertCircle,
  Calendar,
  Droplets,
  RefreshCw,
  Sparkles,
  MapPin,
  SlidersHorizontal,
  ChevronRight,
  Info,
  CheckCircle2,
} from 'lucide-react'
import {
  getGisLocationsApi,
  getLocationHistoryApi,
  getWaterQualityOverviewApi,
} from '../services/api'
import ChartCard from '../components/ChartCard'

const METRIC_CONFIG = {
  ph: {
    key: 'ph',
    label: 'pH',
    unit: '',
    color: '#0e7490',
    description: 'Measures acidity or alkalinity (Dimensionless standard: 6.5 – 8.5)',
    domain: [4, 10],
  },
  dissolved_oxygen: {
    key: 'dissolved_oxygen',
    label: 'Dissolved Oxygen (DO)',
    unit: 'mg/L',
    color: '#059669',
    description: 'Essential oxygen dissolved in water (Higher is better, standard ≥ 5.0 mg/L)',
    domain: ['auto', 'auto'],
  },
  bod: {
    key: 'bod',
    label: 'Biochemical Oxygen Demand (BOD)',
    unit: 'mg/L',
    color: '#d97706',
    description: 'Oxygen consumed by microorganisms to decompose organic waste (standard ≤ 3.0 mg/L)',
    domain: ['auto', 'auto'],
  },
  turbidity: {
    key: 'turbidity',
    label: 'Turbidity',
    unit: 'NTU',
    color: '#7c3aed',
    description: 'Water clarity and suspended particulates (standard ≤ 5.0 NTU)',
    domain: ['auto', 'auto'],
  },
  tds: {
    key: 'tds',
    label: 'Total Dissolved Solids (TDS)',
    unit: 'mg/L',
    color: '#dc2626',
    description: 'Total dissolved mineral salts and organic matter (standard ≤ 500 mg/L)',
    domain: ['auto', 'auto'],
  },
  temperature: {
    key: 'temperature',
    label: 'Temperature',
    unit: '°C',
    color: '#2563eb',
    description: 'Water temperature (°C)',
    domain: ['auto', 'auto'],
  },
}

const PRIMARY_METRICS = ['ph', 'dissolved_oxygen', 'bod', 'turbidity', 'tds']

export default function WaterIntelligence() {
  const [searchParams, setSearchParams] = useSearchParams()
  const locationIdParam = searchParams.get('location_id') || ''

  const [stations, setStations] = useState([])
  const [loadingStations, setLoadingStations] = useState(true)

  const [stationHistory, setStationHistory] = useState(null)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [historyError, setHistoryError] = useState(null)

  const [selectedMetric, setSelectedMetric] = useState('ph')
  const [viewMode, setViewMode] = useState('single') // 'single' | 'all'

  // Date filters
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // Overview stats
  const [overview, setOverview] = useState(null)

  // 1. Load all available monitoring stations (DB water bodies + Maharashtra demo stations)
  useEffect(() => {
    async function loadStations() {
      setLoadingStations(true)
      try {
        const data = await getGisLocationsApi()
        const locList = Array.isArray(data) ? data : []
        setStations(locList)

        // If no location_id specified in query param, default to first station
        if (!locationIdParam && locList.length > 0) {
          const firstId = locList[0].location_id || locList[0].water_body_id
          setSearchParams({ location_id: String(firstId) }, { replace: true })
        }
      } catch (err) {
        console.error('Failed to load monitoring stations:', err)
      } finally {
        setLoadingStations(false)
      }
    }

    loadStations()
  }, [])

  // 2. Load station history whenever locationIdParam, startDate, or endDate changes
  useEffect(() => {
    if (!locationIdParam) return

    async function fetchHistory() {
      setLoadingHistory(true)
      setHistoryError(null)

      try {
        const params = {}
        if (startDate) params.start_date = new Date(startDate).toISOString()
        if (endDate) params.end_date = new Date(endDate).toISOString()

        const historyData = await getLocationHistoryApi(locationIdParam, params)
        setStationHistory(historyData)
      } catch (err) {
        setStationHistory(null)
        setHistoryError(
          err.message ||
            `Failed to load monitoring observations for location '${locationIdParam}'.`
        )
      } finally {
        setLoadingHistory(false)
      }
    }

    fetchHistory()
  }, [locationIdParam, startDate, endDate])

  // 3. Load general database overview for statistical context
  useEffect(() => {
    async function fetchOverview() {
      try {
        const data = await getWaterQualityOverviewApi()
        setOverview(data)
      } catch (_) {}
    }
    fetchOverview()
  }, [])

  const handleStationChange = (newLocationId) => {
    setSearchParams({ location_id: newLocationId })
  }

  const handleResetFilters = () => {
    setStartDate('')
    setEndDate('')
  }

  // Format observations for chart
  const records = stationHistory?.records || []
  const chartData = records.map((r) => ({
    date: r.measured_at
      ? new Date(r.measured_at).toLocaleDateString('en-GB', {
          day: '2-digit',
          month: 'short',
          year: '2-digit',
        })
      : 'Unknown',
    raw_date: r.measured_at,
    ph: r.ph,
    dissolved_oxygen: r.dissolved_oxygen,
    bod: r.bod,
    turbidity: r.turbidity,
    tds: r.tds,
    temperature: r.temperature,
  }))

  const latestRecord = records.length > 0 ? records[records.length - 1] : null
  const activeMetricConfig = METRIC_CONFIG[selectedMetric] || METRIC_CONFIG.ph

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-ocean">
            <Activity className="h-4 w-4" />
            <span>Water Quality Intelligence & Longitudinal Trends</span>
          </div>
          <h1 className="mt-1 text-2xl font-extrabold text-ink sm:text-3xl">
            Station Trend Analysis
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Interactive parameter time-series, latest sensor telemetry, and historical laboratory records.
          </p>
        </div>

        {/* Station Selector Dropdown */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="space-y-1">
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
              Select Monitoring Station
            </label>
            <select
              value={locationIdParam}
              onChange={(e) => handleStationChange(e.target.value)}
              disabled={loadingStations}
              className="input text-xs font-semibold py-2 px-3 min-w-[260px] text-slate-800 bg-white"
            >
              {loadingStations && <option>Loading stations...</option>}
              {stations.map((s) => {
                const sId = s.location_id || s.water_body_id
                return (
                  <option key={sId} value={sId}>
                    {s.is_demo ? '[DEMO] ' : ''}
                    {s.name} ({s.location_name})
                  </option>
                )
              })}
            </select>
          </div>

          <Link
            to="/map"
            className="self-end inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
          >
            <MapPin className="h-3.5 w-3.5 text-ocean" />
            <span>Back to Map</span>
          </Link>
        </div>
      </div>

      {/* Date Range Filter Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-bold text-slate-700 flex items-center gap-1">
            <SlidersHorizontal className="h-3.5 w-3.5 text-ocean" />
            <span>Date Range:</span>
          </span>
          <div className="flex items-center gap-1.5">
            <label className="text-slate-500">From:</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-1 text-xs text-slate-700 focus:outline-ocean"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <label className="text-slate-500">To:</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-1 text-xs text-slate-700 focus:outline-ocean"
            />
          </div>
          {(startDate || endDate) && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="rounded px-2 py-1 text-[11px] font-semibold text-slate-600 hover:text-rose-600 underline"
            >
              Clear Filter
            </button>
          )}
        </div>

        {/* View mode toggle */}
        <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setViewMode('single')}
            className={`rounded px-2.5 py-1 text-xs font-semibold transition-colors ${
              viewMode === 'single'
                ? 'bg-white text-ocean shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Interactive Focus
          </button>
          <button
            type="button"
            onClick={() => setViewMode('all')}
            className={`rounded px-2.5 py-1 text-xs font-semibold transition-colors ${
              viewMode === 'all'
                ? 'bg-white text-ocean shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All Parameters (Separate Units)
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loadingHistory && (
        <div className="rounded-xl border border-slate-200 bg-white p-12 text-center space-y-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-ocean border-t-transparent mx-auto" />
          <p className="text-xs font-semibold text-slate-600">
            Fetching chronological trends for selected station...
          </p>
        </div>
      )}

      {/* Error State */}
      {historyError && !loadingHistory && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800 space-y-3">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-base">Location Not Found</p>
              <p className="text-xs mt-1 text-rose-700">{historyError}</p>
            </div>
          </div>
          {stations.length > 0 && (
            <div className="pt-2">
              <button
                type="button"
                onClick={() =>
                  handleStationChange(
                    stations[0].location_id || stations[0].water_body_id
                  )
                }
                className="rounded-lg bg-rose-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 transition-colors"
              >
                Switch to Available Station ({stations[0].name})
              </button>
            </div>
          )}
        </div>
      )}

      {/* Active Station Content */}
      {stationHistory && !loadingHistory && (
        <div className="space-y-6">
          {/* Station Metadata Card */}
          <div className="rounded-xl border border-slate-200/90 bg-white p-5 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-ink">
                    {stationHistory.name}
                  </h2>
                  {stationHistory.is_demo && (
                    <span className="rounded bg-amber-100 border border-amber-300 px-2 py-0.5 text-[11px] font-bold text-amber-900 uppercase tracking-wide">
                      DEMO DATA
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5 capitalize">
                  {stationHistory.water_body_type} &middot; {stationHistory.location_name}
                </p>
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-600">
                <span className="flex items-center gap-1 font-mono">
                  <MapPin className="h-3.5 w-3.5 text-slate-400" />
                  {stationHistory.latitude.toFixed(4)}, {stationHistory.longitude.toFixed(4)}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                  {records.length} Observations Analyzed
                </span>
              </div>
            </div>

            {/* Synthetic Data Notice */}
            {stationHistory.is_demo && (
              <div className="rounded-lg bg-amber-50/80 border border-amber-200 p-3 text-xs text-amber-900 flex items-start gap-2.5">
                <Info className="h-4 w-4 text-amber-700 shrink-0 mt-0.5" />
                <p className="leading-relaxed text-[11.5px]">
                  <strong>Demonstration Dataset Notice:</strong> This monitoring station contains 
                  synthetic observations for UI validation and trend visualization. 
                  It does not reflect verified regulatory compliance or live sensor telemetry.
                </p>
              </div>
            )}

            {/* Latest Measurements KPI Row */}
            {latestRecord && (
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Latest Validated Observation (
                  {new Date(latestRecord.measured_at).toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                  })}
                  )
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                    <span className="text-[11px] font-medium text-slate-500 block">pH Level</span>
                    <span className="text-xl font-extrabold text-ocean mt-0.5 block">
                      {latestRecord.ph !== null ? latestRecord.ph : '—'}
                    </span>
                    <span className="text-[10px] text-slate-400">Target: 6.5 – 8.5</span>
                  </div>

                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                    <span className="text-[11px] font-medium text-slate-500 block">Dissolved Oxygen</span>
                    <span className="text-xl font-extrabold text-emerald-600 mt-0.5 block">
                      {latestRecord.dissolved_oxygen !== null ? `${latestRecord.dissolved_oxygen} mg/L` : '—'}
                    </span>
                    <span className="text-[10px] text-slate-400">Target: ≥ 5.0 mg/L</span>
                  </div>

                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                    <span className="text-[11px] font-medium text-slate-500 block">BOD</span>
                    <span className="text-xl font-extrabold text-amber-600 mt-0.5 block">
                      {latestRecord.bod !== null ? `${latestRecord.bod} mg/L` : '—'}
                    </span>
                    <span className="text-[10px] text-slate-400">Target: ≤ 3.0 mg/L</span>
                  </div>

                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                    <span className="text-[11px] font-medium text-slate-500 block">Turbidity</span>
                    <span className="text-xl font-extrabold text-purple-600 mt-0.5 block">
                      {latestRecord.turbidity !== null ? `${latestRecord.turbidity} NTU` : '—'}
                    </span>
                    <span className="text-[10px] text-slate-400">Target: ≤ 5.0 NTU</span>
                  </div>

                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                    <span className="text-[11px] font-medium text-slate-500 block">TDS</span>
                    <span className="text-xl font-extrabold text-rose-600 mt-0.5 block">
                      {latestRecord.tds !== null ? `${latestRecord.tds} mg/L` : '—'}
                    </span>
                    <span className="text-[10px] text-slate-400">Target: ≤ 500 mg/L</span>
                  </div>

                  <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                    <span className="text-[11px] font-medium text-slate-500 block">Temperature</span>
                    <span className="text-xl font-extrabold text-blue-600 mt-0.5 block">
                      {latestRecord.temperature !== null ? `${latestRecord.temperature} °C` : '—'}
                    </span>
                    <span className="text-[10px] text-slate-400">Ambient water</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Charts Section */}
          {chartData.length === 0 ? (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-xs text-slate-500">
              No historical observations found for the specified date range.
            </div>
          ) : viewMode === 'single' ? (
            /* Interactive Focus Single Chart */
            <ChartCard
              title={`${activeMetricConfig.label} Trend Analysis`}
              subtitle={activeMetricConfig.description}
              action={
                <div className="flex flex-wrap items-center gap-1.5">
                  {Object.values(METRIC_CONFIG).map((m) => (
                    <button
                      key={m.key}
                      type="button"
                      onClick={() => setSelectedMetric(m.key)}
                      className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors ${
                        selectedMetric === m.key
                          ? 'bg-ocean text-white shadow-xs'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {m.label} {m.unit ? `(${m.unit})` : ''}
                    </button>
                  ))}
                </div>
              }
            >
              <div className="h-72 sm:h-80 pt-3">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" fontSize={11} stroke="#64748b" />
                    <YAxis
                      fontSize={11}
                      stroke="#64748b"
                      domain={activeMetricConfig.domain}
                      unit={activeMetricConfig.unit ? ` ${activeMetricConfig.unit}` : ''}
                    />
                    <Tooltip
                      formatter={(val) => [
                        `${val} ${activeMetricConfig.unit}`.trim(),
                        activeMetricConfig.label,
                      ]}
                      labelFormatter={(lbl) => `Observation Date: ${lbl}`}
                    />
                    <Line
                      type="monotone"
                      dataKey={selectedMetric}
                      name={activeMetricConfig.label}
                      stroke={activeMetricConfig.color}
                      strokeWidth={2.5}
                      dot={{ r: 3.5, fill: activeMetricConfig.color }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          ) : (
            /* Multi-Chart Grid: Separate Units on Dedicated Axes */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
                  Parameter Breakdown (Strictly Isolated Measurement Units)
                </h3>
                <span className="text-xs text-slate-500">
                  Each parameter plotted independently to avoid false unit conflation
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {PRIMARY_METRICS.map((key) => {
                  const cfg = METRIC_CONFIG[key]
                  return (
                    <div
                      key={key}
                      className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs space-y-2"
                    >
                      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                        <div>
                          <h4 className="font-bold text-sm text-slate-800">{cfg.label}</h4>
                          <p className="text-[11px] text-slate-500">{cfg.description}</p>
                        </div>
                        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-mono font-bold text-slate-700">
                          {cfg.unit || 'pH units'}
                        </span>
                      </div>
                      <div className="h-52 pt-2">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="date" fontSize={10} stroke="#64748b" />
                            <YAxis
                              fontSize={10}
                              stroke="#64748b"
                              domain={cfg.domain}
                              unit={cfg.unit ? ` ${cfg.unit}` : ''}
                            />
                            <Tooltip
                              formatter={(val) => [`${val} ${cfg.unit}`.trim(), cfg.label]}
                              labelFormatter={(lbl) => `Date: ${lbl}`}
                            />
                            <Line
                              type="monotone"
                              dataKey={key}
                              stroke={cfg.color}
                              strokeWidth={2}
                              dot={{ r: 2.5, fill: cfg.color }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Chronological Observation Records Table */}
          <div className="rounded-xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-4">
            <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-ink">
                  Chronological Sampling Logs
                </h3>
                <p className="text-xs text-slate-500">
                  Historical water quality observations logged for {stationHistory.name}
                </p>
              </div>
              <span className="text-xs font-semibold text-slate-500">
                {records.length} Record{records.length === 1 ? '' : 's'}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-100 text-slate-500 font-semibold bg-slate-50/50">
                  <tr>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">pH</th>
                    <th className="py-2.5 px-3">DO (mg/L)</th>
                    <th className="py-2.5 px-3">BOD (mg/L)</th>
                    <th className="py-2.5 px-3">Turbidity (NTU)</th>
                    <th className="py-2.5 px-3">TDS (mg/L)</th>
                    <th className="py-2.5 px-3">Temp (°C)</th>
                    <th className="py-2.5 px-3">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {records.map((r, i) => (
                    <tr key={r.id || i} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-2.5 px-3 font-medium text-slate-700">
                        {r.measured_at
                          ? new Date(r.measured_at).toLocaleDateString('en-GB', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric',
                            })
                          : '—'}
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-ink">{r.ph ?? '—'}</td>
                      <td className="py-2.5 px-3">{r.dissolved_oxygen ?? '—'}</td>
                      <td className="py-2.5 px-3">{r.bod ?? '—'}</td>
                      <td className="py-2.5 px-3">{r.turbidity ?? '—'}</td>
                      <td className="py-2.5 px-3">{r.tds ?? '—'}</td>
                      <td className="py-2.5 px-3">{r.temperature ?? '—'}</td>
                      <td className="py-2.5 px-3">
                        {r.is_demo ? (
                          <span className="rounded bg-amber-50 text-amber-800 border border-amber-200 px-1.5 py-0.5 text-[10px] font-bold">
                            DEMO
                          </span>
                        ) : (
                          <span className="rounded bg-emerald-50 text-emerald-800 border border-emerald-200 px-1.5 py-0.5 text-[10px] font-bold">
                            VERIFIED
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
