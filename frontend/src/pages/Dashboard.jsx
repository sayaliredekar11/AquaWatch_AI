import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  TestTube2,
  MapPin,
  Activity,
  Users,
  AlertCircle,
  RefreshCw,
  PlusCircle,
  Calendar,
  Search,
  Download,
  ExternalLink,
  FileText,
} from 'lucide-react'
import {
  getDashboardSummaryApi,
  getOfficialDashboardSummaryApi,
  getRecentMeasurementsApi,
  getReportDownloadUrl,
} from '../services/api'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [officialSummary, setOfficialSummary] = useState(null)
  const [recentMeasurements, setRecentMeasurements] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [sumData, offData, recents] = await Promise.all([
        getDashboardSummaryApi(),
        getOfficialDashboardSummaryApi().catch((err) => {
          console.warn('Official summary fetch warning:', err.message)
          return null
        }),
        getRecentMeasurementsApi(15),
      ])

      setSummary(sumData)
      setOfficialSummary(offData)
      setRecentMeasurements(Array.isArray(recents) ? recents : [])
    } catch (err) {
      setError(err.message || 'Failed to load dashboard analytics from backend.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  const cards = [
    {
      title: 'Total Measurements',
      value: summary ? summary.total_measurements : '—',
      description: 'Validated chemical & physical logs',
      icon: TestTube2,
      iconBg: 'bg-cyan-100/70 text-ocean',
    },
    {
      title: 'Monitored Locations',
      value: summary ? summary.total_water_bodies : '—',
      description: summary
        ? `${summary.mapped_locations} mapped with GPS coordinates`
        : 'Water bodies tracked',
      icon: MapPin,
      iconBg: 'bg-cyan-100/70 text-ocean',
    },
    {
      title: 'Recent Activity',
      value: officialSummary ? officialSummary.measurements_last_7_days : '—',
      description: 'Samples logged in past 7 days',
      icon: Activity,
      iconBg: 'bg-emerald-100/80 text-emerald-600',
    },
    {
      title: 'Registered Users',
      value: officialSummary ? officialSummary.total_registered_users : '—',
      description: 'Platform user accounts',
      icon: Users,
      iconBg: 'bg-indigo-100/80 text-indigo-600',
    },
  ]

  const filteredMeasurements = recentMeasurements.filter((m) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase().trim()
    return (
      (m.sample_id && m.sample_id.toLowerCase().includes(q)) ||
      (m.report_id && m.report_id.toLowerCase().includes(q)) ||
      (m.water_body_name && m.water_body_name.toLowerCase().includes(q)) ||
      (m.location_name && m.location_name.toLowerCase().includes(q))
    )
  })

  return (
    <div className="min-h-[calc(100vh-65px)] bg-mist px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8 animate-fade-in">
        {/* Header / Hero */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-ocean">
              LABORATORY OPERATIONS
            </span>
            <h1 className="mt-1 text-3xl font-extrabold text-ink sm:text-4xl">
              Lab Dashboard
            </h1>
            <p className="mt-1 text-sm text-slate-600 sm:text-base">
              Real-time monitoring metrics, historical test audits, and certified PDF laboratory reports.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadDashboardData}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-all duration-200 active:scale-[0.98] shadow-xs disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <Link
              to="/test"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-ocean px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-[#0c627a] active:scale-[0.98]"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Record Sample</span>
            </Link>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 flex items-start gap-3 animate-fade-slide-down">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-rose-600" />
            <div className="flex-1">
              <p className="font-semibold">Unable to load dashboard records</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
            <button
              onClick={loadDashboardData}
              className="text-xs font-bold underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 animate-fade-slide-up">
          {cards.map((card) => {
            const Icon = card.icon
            return (
              <div
                key={card.title}
                className="relative overflow-hidden rounded-xl border border-slate-200/80 bg-white p-5 shadow-xs card-hover"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    {card.title}
                  </span>
                  <div
                    className={`flex h-9 w-9 items-center justify-center rounded-lg ${card.iconBg}`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-extrabold text-ink sm:text-3xl">
                    {loading ? (
                      <span className="inline-block h-8 w-16 animate-pulse rounded-md bg-slate-100" />
                    ) : (
                      card.value
                    )}
                  </div>
                  <p className="mt-1 text-xs text-slate-500">{card.description}</p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Recent Measurements Section */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-lg font-bold text-ink">Recent Test Logs & Certified Reports</h2>
              <p className="text-xs text-slate-500">
                Latest water quality records saved directly to PostgreSQL with certified PDF reports
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search Sample ID, Report ID, or Water Body..."
                  className="w-56 sm:w-64 rounded-lg border border-slate-200 bg-slate-50/50 py-1.5 pl-8 pr-3 text-xs text-slate-800 focus:border-ocean focus:bg-white focus:outline-none"
                />
              </div>
              <Link
                to="/test"
                className="text-xs font-semibold text-ocean hover:text-cyan-800 transition-colors shrink-0"
              >
                + Log New Record
              </Link>
            </div>
          </div>

          {loading ? (
            <div className="py-12 text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-ocean border-t-transparent" />
              <p className="mt-3 text-xs text-slate-500 font-medium">Fetching measurements...</p>
            </div>
          ) : filteredMeasurements.length === 0 ? (
            <div className="py-12 text-center space-y-2">
              <TestTube2 className="h-8 w-8 text-slate-400 mx-auto" />
              <p className="font-semibold text-slate-700 text-sm">No measurements found</p>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                {searchQuery ? 'No records match your search query.' : 'Laboratory measurements recorded via the Test Water page will appear here.'}
              </p>
              <Link
                to="/test"
                className="inline-block mt-2 rounded-lg bg-ocean px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#0c627a] transition-colors"
              >
                Log First Test
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-xs font-semibold text-slate-500">
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Sample ID</th>
                    <th className="py-2.5 px-3">Report ID</th>
                    <th className="py-2.5 px-3">Water Body</th>
                    <th className="py-2.5 px-3">Location</th>
                    <th className="py-2.5 px-3">pH</th>
                    <th className="py-2.5 px-3">DO (mg/L)</th>
                    <th className="py-2.5 px-3">WQI Score</th>
                    <th className="py-2.5 px-3">WQI Grade</th>
                    <th className="py-2.5 px-3 text-right">Report</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {filteredMeasurements.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-3 text-slate-500 whitespace-nowrap">
                        {m.measured_at
                          ? new Date(m.measured_at).toLocaleDateString('en-GB', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric',
                            })
                          : '—'}
                      </td>
                      <td className="py-3 px-3 font-mono font-bold text-ocean">
                        {m.sample_id || `SMP-${m.id}`}
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-600">
                        {m.report_id || `REP-${m.id}`}
                      </td>
                      <td className="py-3 px-3 font-semibold text-ink">
                        <Link
                          to={`/intelligence?location_id=${m.water_body_id}`}
                          className="hover:text-ocean flex items-center gap-1 group"
                        >
                          <span>{m.water_body_name}</span>
                          <ExternalLink className="h-2.5 w-2.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </Link>
                      </td>
                      <td className="py-3 px-3 text-slate-600">{m.location_name}</td>
                      <td className="py-3 px-3 font-medium text-slate-800">{m.ph ?? '—'}</td>
                      <td className="py-3 px-3 text-slate-700">{m.dissolved_oxygen ?? '—'}</td>
                      <td className="py-3 px-3 font-mono font-bold text-indigo-900">
                        {m.wqi_score !== null && m.wqi_score !== undefined ? m.wqi_score.toFixed(2) : '—'}
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-[10px] font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                          {m.wqi_category || '—'}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => window.open(getReportDownloadUrl(m.report_id || m.id), '_blank')}
                          className="inline-flex items-center gap-1 rounded bg-ocean/10 hover:bg-ocean/20 text-ocean px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer"
                          title="Download Official PDF Report"
                        >
                          <Download className="h-3 w-3" />
                          <span>PDF</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
