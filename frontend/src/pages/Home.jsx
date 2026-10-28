import { Link } from 'react-router-dom'
import { Gauge, History, AlertTriangle, Map, ArrowRight, FlaskConical, LayoutDashboard } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const features = [
  {
    icon: Gauge,
    title: 'AI WQI Assessment',
    text: 'Transform laboratory measurements into an explainable Water Quality Index score and quality category.',
  },
  {
    icon: Map,
    title: 'GIS Map Visualization',
    text: 'Interactively monitor water quality across western Maharashtra locations with spatial resolution.',
  },
  {
    icon: History,
    title: 'Historical Intelligence',
    text: 'Track parameter trends and historical changes month-by-month across key monitoring sites.',
  },
  {
    icon: AlertTriangle,
    title: 'Anomaly Indicators',
    text: 'Flag measurements that deviate significantly from established historical baseline ranges.',
  },
]

const steps = [
  'Measure',
  'Validate',
  'Analyze',
  'Explain',
  'Compare',
  'Detect',
  'Visualize',
]

export default function Home() {
  const { user, isLabAuthority } = useAuth()

  return (
    <div className="space-y-12 pb-12">
      {/* Hero Banner */}
      <section className="bg-ink text-white py-16 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <span className="inline-block rounded-full bg-cyan-950 px-3 py-1 text-xs font-bold uppercase tracking-wider text-cyan-400 border border-cyan-800/50 mb-3">
            AI-POWERED WATER INTELLIGENCE
          </span>
          <h1 className="text-4xl font-extrabold sm:text-5xl text-white tracking-tight leading-tight max-w-4xl">
            Understand Water Quality. <br className="hidden sm:inline" />
            <span className="text-cyan-300">Before It Becomes a Problem.</span>
          </h1>
          <p className="mt-4 max-w-2xl text-slate-300 text-base sm:text-lg leading-relaxed">
            Transform laboratory-measured water parameters into transparent, explainable Water Quality Index (WQI) assessments and location-based insights.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              to="/map"
              className="btn-primary inline-flex items-center gap-2 font-semibold shadow-md px-5 py-3 text-sm"
            >
              <span>Explore Water Map</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            {isLabAuthority ? (
              <Link
                to="/dashboard"
                className="btn border border-cyan-300 text-white hover:bg-white/10 font-semibold px-5 py-3 text-sm"
              >
                Go to Lab Dashboard
              </Link>
            ) : (
              <Link
                to="/about"
                className="btn border border-slate-600 text-slate-200 hover:bg-white/10 hover:text-white font-semibold px-5 py-3 text-sm"
              >
                Learn Methodology
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Main Content Container */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Core Features Grid */}
        <section className="space-y-6">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-2xl font-extrabold text-ink sm:text-3xl">Platform Capabilities</h2>
            <p className="text-sm text-slate-600">
              Connecting reliable laboratory measurements with machine-learning-based assessment.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {features.map((f) => {
              const Icon = f.icon
              return (
                <div
                  key={f.title}
                  className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-sm transition-shadow hover:shadow-md space-y-3"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-100/70 text-ocean">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-bold text-slate-900 text-base">{f.title}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{f.text}</p>
                </div>
              )
            })}
          </div>
        </section>

        {/* Process Flow */}
        <section className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm text-center space-y-6">
          <div>
            <h2 className="text-xl font-bold text-ink">Analytical Workflow</h2>
            <p className="text-xs sm:text-sm text-slate-600 mt-1">
              Traceable process from raw laboratory measurement to interpreted result.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2 text-xs sm:text-sm">
            {steps.map((s, i) => (
              <span key={s} className="flex items-center gap-2">
                <span className="rounded-full bg-cyan-50 px-3.5 py-1.5 font-bold text-ocean border border-cyan-200/80 shadow-2xs">
                  {s}
                </span>
                {i < steps.length - 1 && <span className="text-slate-300 font-bold">→</span>}
              </span>
            ))}
          </div>
        </section>

        {/* Role Access Banner */}
        <section className="rounded-xl bg-[#071e2b] text-white p-6 sm:p-8 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                ROLE-BASED PORTAL ACCESS
              </span>
              <h3 className="text-xl font-bold text-white">Public Visitors & Laboratory Authorities</h3>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Public visitors can freely browse interactive GIS maps, regional water quality averages, and historical intelligence without needing an account. Authorized laboratory personnel sign in to test water samples, calculate WQI assessments, and manage monitored sites.
              </p>
            </div>

            <div className="shrink-0 flex items-center gap-3">
              {isLabAuthority ? (
                <Link
                  to="/dashboard"
                  className="btn bg-cyan-500 text-slate-950 hover:bg-cyan-400 font-semibold text-xs px-4 py-2.5 flex items-center gap-2 shadow-sm"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  <span>Open Lab Dashboard</span>
                </Link>
              ) : (
                <Link
                  to="/login"
                  className="btn bg-ocean text-white hover:bg-[#0c627a] font-semibold text-xs px-4 py-2.5 flex items-center gap-2 shadow-sm"
                >
                  <FlaskConical className="h-4 w-4" />
                  <span>Lab Authority Portal</span>
                </Link>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
