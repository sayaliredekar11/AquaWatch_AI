import { useState, useEffect } from 'react'
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
  Info,
} from 'lucide-react'
import {
  getWaterQualityOverviewApi,
  getRecentMeasurementsApi,
  getWaterBodiesApi,
} from '../services/api'
import ChartCard from '../components/ChartCard'

const METRIC_OPTIONS = [
  { key: 'ph', label: 'pH', unit: '' },
  { key: 'dissolved_oxygen', label: 'Dissolved Oxygen (DO)', unit: 'mg/L' },
  { key: 'bod', label: 'Biochemical Oxygen Demand (BOD)', unit: 'mg/L' },
  { key: 'turbidity', label: 'Turbidity', unit: 'NTU' },
  { key: 'tds', label: 'Total Dissolved Solids (TDS)', unit: 'mg/L' },
  { key: 'temperature', label: 'Temperature', unit: '°C' },
]

export default function WaterIntelligence() {
  const [overview, setOverview] = useState(null)
  const [recentMeasurements, setRecentMeasurements] = useState([])
  const [waterBodies, setWaterBodies] = useState([])
  const [selectedWaterBodyId, setSelectedWaterBodyId] = useState('')
  const [selectedMetric, setSelectedMetric] = useState('ph')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadData = async (wbId = selectedWaterBodyId) => {
    setLoading(true)
    setError(null)
    try {
      const params = wbId ? { water_body_id: wbId } : {}
      const [overviewData, recents, bodies] = await Promise.all([
        getWaterQualityOverviewApi(params),
        getRecentMeasurementsApi(30),
        getWaterBodiesApi(0, 100),
      ])

      setOverview(overviewData)
      setRecentMeasurements(Array.isArray(recents) ? recents : [])
      setWaterBodies(Array.isArray(bodies) ? bodies : [])
    } catch (err) {
      setError(err.message || 'Failed to load water quality intelligence data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [selectedWaterBodyId])

  // Filter measurements for chart if a specific water body is selected
  const chartSource = selectedWaterBodyId
    ? recentMeasurements.filter(
        (m) => m.water_body_id.toString() === selectedWaterBodyId.toString()
      )
    : recentMeasurements

  // Format chronological timeline data for Recharts
  const chartData = [...chartSource]
    .reverse()
    .filter((m) => m[selectedMetric] !== null && m[selectedMetric] !== undefined)
    .map((m) => ({
      date: m.measured_at
        ? new Date(m.measured_at).toLocaleDateString('en-GB', {
            day: '2-digit',
            month: 'short',
          })
        : 'Unknown',
      value: Number(m[selectedMetric]),
      location: m.water_body_name,
    }))

  const activeMetricObj = METRIC_OPTIONS.find((m) => m.key === selectedMetric) || METRIC_OPTIONS[0]

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-ocean">
            ANALYTICS & INTELLIGENCE
          </span>
          <h1 className="mt-1 text-2xl font-extrabold text-ink sm:text-3xl">
            Water Quality Intelligence
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Real parameter averages and longitudinal measurement trends calculated via PostgreSQL SQL aggregations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {waterBodies.length > 0 && (
            <select
              value={selectedWaterBodyId}
              onChange={(e) => setSelectedWaterBodyId(e.target.value)}
              className="input text-xs font-medium py-1.5"
            >
              <option value="">All Water Bodies</option>
              {waterBodies.map((wb) => (
                <option key={wb.id} value={wb.id}>
                  {wb.name}
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={() => loadData(selectedWaterBodyId)}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-xs disabled:opacity-50"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error notification */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-rose-600" />
          <div className="flex-1">
            <p className="font-semibold">Unable to fetch intelligence statistics</p>
            <p className="text-xs mt-0.5">{error}</p>
          </div>
          <button
            onClick={() => loadData(selectedWaterBodyId)}
            className="text-xs font-bold underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase">Records Analyzed</span>
          <p className="text-2xl font-extrabold text-ink mt-1">
            {overview ? overview.total_records_analyzed : '—'}
          </p>
          <span className="text-[11px] text-slate-400">Total samples in database</span>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase">Average pH</span>
          <p className="text-2xl font-extrabold text-ocean mt-1">
            {overview?.average_ph?.value !== null && overview?.average_ph?.value !== undefined
              ? overview.average_ph.value
              : '—'}
          </p>
          <span className="text-[11px] text-slate-400">Standard range 6.5 – 8.5</span>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase">Average DO</span>
          <p className="text-2xl font-extrabold text-emerald-600 mt-1">
            {overview?.average_dissolved_oxygen?.value !== null &&
            overview?.average_dissolved_oxygen?.value !== undefined
              ? `${overview.average_dissolved_oxygen.value} mg/L`
              : '—'}
          </p>
          <span className="text-[11px] text-slate-400">Dissolved oxygen</span>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase">Latest Sampling</span>
          <p className="text-sm font-bold text-slate-800 mt-2 truncate">
            {overview?.latest_measurement_timestamp
              ? new Date(overview.latest_measurement_timestamp).toLocaleDateString('en-GB', {
                  day: '2-digit',
                  month: 'short',
                  year: 'numeric',
                })
              : 'No records'}
          </p>
          <span className="text-[11px] text-slate-400">Most recent entry</span>
        </div>
      </div>

      {/* Parameter Cards Overview */}
      {overview && (
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-xs space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Statistical Averages by Parameter (SQL AVG)
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 text-center">
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">pH</span>
              <p className="font-extrabold text-base text-ink mt-0.5">
                {overview.average_ph?.value ?? '—'}
              </p>
            </div>
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">DO</span>
              <p className="font-extrabold text-base text-ink mt-0.5">
                {overview.average_dissolved_oxygen?.value ?? '—'}
              </p>
              <span className="text-[10px] text-slate-400">mg/L</span>
            </div>
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">BOD</span>
              <p className="font-extrabold text-base text-ink mt-0.5">
                {overview.average_bod?.value ?? '—'}
              </p>
              <span className="text-[10px] text-slate-400">mg/L</span>
            </div>
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">Turbidity</span>
              <p className="font-extrabold text-base text-ink mt-0.5">
                {overview.average_turbidity?.value ?? '—'}
              </p>
              <span className="text-[10px] text-slate-400">NTU</span>
            </div>
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">TDS</span>
              <p className="font-extrabold text-base text-ink mt-0.5">
                {overview.average_tds?.value ?? '—'}
              </p>
              <span className="text-[10px] text-slate-400">mg/L</span>
            </div>
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">EC</span>
              <p className="font-extrabold text-base text-ink mt-0.5">
                {overview.average_electrical_conductivity?.value ?? '—'}
              </p>
              <span className="text-[10px] text-slate-400">µS/cm</span>
            </div>
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">Nitrate</span>
              <p className="font-extrabold text-base text-ink mt-0.5">
                {overview.average_nitrate?.value ?? '—'}
              </p>
              <span className="text-[10px] text-slate-400">mg/L</span>
            </div>
            <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-100">
              <span className="text-xs text-slate-500 font-medium">Temp</span>
              <p className="font-extrabold text-base text-ink mt-0.5">
                {overview.average_temperature?.value ?? '—'}
              </p>
              <span className="text-[10px] text-slate-400">°C</span>
            </div>
          </div>
        </div>
      )}

      {/* Historical Trend Chart */}
      <ChartCard
        title={`${activeMetricObj.label} Measurement Trend`}
        subtitle="Chronological sequence of validated samples from PostgreSQL"
        action={
          <select
            className="input text-xs w-auto py-1 font-medium"
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
          >
            {METRIC_OPTIONS.map((opt) => (
              <option key={opt.key} value={opt.key}>
                {opt.label}
              </option>
            ))}
          </select>
        }
      >
        <div className="h-64 sm:h-72">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              No historical data points available for this parameter.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" fontSize={11} stroke="#64748b" />
                <YAxis fontSize={11} stroke="#64748b" domain={['auto', 'auto']} />
                <Tooltip
                  formatter={(val) => [`${val} ${activeMetricObj.unit}`, activeMetricObj.label]}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  name={activeMetricObj.label}
                  stroke="#0e7490"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#0e7490' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </ChartCard>

      {/* Machine Learning Prediction Status Notice */}
      <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-xs text-amber-900 flex items-start gap-3">
        <Sparkles className="h-5 w-5 shrink-0 mt-0.5 text-amber-600" />
        <div className="space-y-1">
          <p className="font-semibold text-amber-950">Machine Learning Model Integration Status</p>
          <p className="text-amber-800">
            The FastAPI backend exposes endpoints for predictive pollution classification. Model training and evaluation are conducted independently by the ML team. In default operating mode, the system presents strictly validated laboratory measurements rather than unverified synthetic predictions.
          </p>
        </div>
      </div>

      {/* Testing History Table */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-4">
        <div className="border-b border-slate-100 pb-3">
          <h2 className="text-base font-bold text-ink">Recent Measurement Records</h2>
          <p className="text-xs text-slate-500">Validated physical and chemical logs</p>
        </div>

        {recentMeasurements.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-6">
            No measurement history available in database.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 text-slate-500 font-semibold">
                <tr>
                  <th className="py-2.5 pr-4">ID</th>
                  <th className="py-2.5 pr-4">Water Body</th>
                  <th className="py-2.5 pr-4">Location</th>
                  <th className="py-2.5 pr-4">pH</th>
                  <th className="py-2.5 pr-4">DO</th>
                  <th className="py-2.5 pr-4">Turbidity</th>
                  <th className="py-2.5 pr-4">TDS</th>
                  <th className="py-2.5">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentMeasurements.slice(0, 10).map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/70">
                    <td className="py-2.5 pr-4 font-mono font-medium text-slate-600">#{r.id}</td>
                    <td className="py-2.5 pr-4 font-semibold text-ink">{r.water_body_name}</td>
                    <td className="py-2.5 pr-4 text-slate-600">{r.location_name}</td>
                    <td className="py-2.5 pr-4">{r.ph ?? '—'}</td>
                    <td className="py-2.5 pr-4">{r.dissolved_oxygen ? `${r.dissolved_oxygen} mg/L` : '—'}</td>
                    <td className="py-2.5 pr-4">{r.turbidity ? `${r.turbidity} NTU` : '—'}</td>
                    <td className="py-2.5 pr-4">{r.tds ? `${r.tds} mg/L` : '—'}</td>
                    <td className="py-2.5 text-slate-500">
                      {r.measured_at
                        ? new Date(r.measured_at).toLocaleDateString('en-GB', {
                            day: '2-digit',
                            month: 'short',
                          })
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
