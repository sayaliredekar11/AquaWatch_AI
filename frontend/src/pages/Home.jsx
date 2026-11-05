import { Link } from 'react-router-dom'
import {
  Droplets,
  MapPin,
  Brain,
  FlaskConical,
  BarChart3,
  ShieldCheck,
  ArrowRight,
  Waves,
  Activity,
  Layers,
  Compass,
  FileText,
  Users,
  CheckCircle2,
  Sparkles,
  ChevronRight,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Reveal from '../components/Reveal'

export default function Home() {
  const { user, isLabAuthority } = useAuth()

  // 4 Core Capabilities (Concise & Actionable for Home)
  const coreCapabilities = [
    {
      icon: MapPin,
      title: 'Interactive Water Quality Map',
      description:
        'Explore geo-referenced monitoring stations across Maharashtra with live status pins, place search, and water-body telemetry.',
      link: '/map',
      actionLabel: 'Launch Map',
      badge: 'GIS Mapping',
      color: 'text-emerald-700 bg-emerald-100/70 border-emerald-200',
    },
    {
      icon: Brain,
      title: 'ML WQI Assessment',
      description:
        'Transform multi-parameter laboratory observations into an explainable Water Quality Index score and standardized quality grade.',
      link: '/intelligence',
      actionLabel: 'View Intelligence',
      badge: 'Machine Learning',
      color: 'text-indigo-700 bg-indigo-100/70 border-indigo-200',
    },
    {
      icon: BarChart3,
      title: 'Station Trend Analytics',
      description:
        'Inspect chronological time-series trends, historical observations, and parameter baseline shifts across rivers and reservoirs.',
      link: '/intelligence',
      actionLabel: 'Analyze Trends',
      badge: 'Time-Series',
      color: 'text-blue-700 bg-blue-100/70 border-blue-200',
    },
    {
      icon: FlaskConical,
      title: 'Certified Laboratory Testing',
      description:
        'Authorized laboratories input 14 physical, chemical, and biological parameters, audit samples, and generate official PDF reports.',
      link: isLabAuthority ? '/test' : '/login',
      actionLabel: isLabAuthority ? 'Record Sample' : 'Lab Authority Login',
      badge: isLabAuthority ? 'Active Access' : 'Authorized Only',
      color: 'text-cyan-700 bg-cyan-100/70 border-cyan-200',
    },
  ]

  // Concise 3-Step Visual Workflow for Landing Experience
  const quickWorkflow = [
    {
      step: '01',
      title: 'Record Lab Sample',
      desc: 'Laboratory authorities log 14 validated physical-chemical parameters tied to specific monitoring coordinates.',
      icon: FlaskConical,
    },
    {
      step: '02',
      title: 'Machine Learning Inference',
      desc: 'The trained decision tree evaluates 12 model features to compute a standardized WQI score and safety grade.',
      icon: Brain,
    },
    {
      step: '03',
      title: 'Spatial & Historical Insights',
      desc: 'Results are immediately visible on the state-wide GIS map, charted across timelines, and exportable as certified PDFs.',
      icon: MapPin,
    },
  ]

  return (
    <div className="space-y-16 pb-16 min-h-screen text-ink antialiased">
      {/* =================================================================== */}
      {/* SECTION 1: HERO SECTION (ENGAGING PRODUCT LANDING)                  */}
      {/* =================================================================== */}
      <section className="relative overflow-hidden bg-gradient-to-b from-[#071e2b] via-[#0b2a3a] to-[#071e2b] text-white pt-16 pb-20 sm:pt-20 sm:pb-24 px-4 sm:px-6 lg:px-8 border-b border-cyan-900/40">
        {/* Subtle Water Light/Grid Effects */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900/25 via-transparent to-transparent pointer-events-none" />
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none animate-float-slow" />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 rounded-full bg-ocean/15 blur-3xl pointer-events-none animate-float-delayed" />

        <div className="relative mx-auto max-w-7xl">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            {/* Left Content Column */}
            <div className="lg:col-span-7 space-y-5 animate-fade-slide-up">
              <div className="inline-flex items-center gap-2 rounded-full bg-cyan-950/80 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-cyan-300 border border-cyan-700/60 shadow-xs">
                <Droplets className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                <span>Environmental Technology Platform</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight">
                Smarter Water Monitoring for a Sustainable Future
              </h1>

              <h2 className="text-lg sm:text-xl font-bold text-cyan-300 leading-snug">
                Intelligent Water Quality Monitoring and Pollution Prediction
              </h2>

              <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
                AquaWatch AI brings water quality information together through laboratory testing,
                machine learning-based WQI prediction, and interactive location-based monitoring.
                Explore water quality results and support informed environmental decisions through
                data-driven insights.
              </p>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-wrap items-center gap-3.5">
                <Link
                  to="/map"
                  className="btn-primary inline-flex items-center gap-2 text-xs sm:text-sm font-semibold px-5 py-3 shadow-md hover:shadow-lg transition-all active:scale-[0.98]"
                >
                  <MapPin className="h-4 w-4" />
                  <span>Explore Water Quality Map</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>

                <Link
                  to="/about"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-600 bg-white/5 px-4 py-3 text-xs sm:text-sm font-semibold text-slate-200 hover:bg-white/10 hover:text-white transition-all active:scale-[0.98]"
                >
                  <span>Learn About Our Project</span>
                  <ArrowRight className="h-3.5 w-3.5 text-cyan-400" />
                </Link>

                {isLabAuthority && (
                  <Link
                    to="/dashboard"
                    className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-400/40 bg-cyan-950/60 px-4 py-3 text-xs sm:text-sm font-semibold text-cyan-300 hover:bg-cyan-900/60 transition-colors"
                  >
                    <FlaskConical className="h-4 w-4" />
                    <span>Lab Portal</span>
                  </Link>
                )}
              </div>

              {/* Trust Indicators */}
              <div className="pt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 border-t border-cyan-900/60 text-xs text-slate-300">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>Validated Lab Measurements</span>
                </div>
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>ML WQI Classification</span>
                </div>
                <div className="flex items-center gap-2 col-span-2 sm:col-span-1">
                  <Compass className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>Geographic Tracking</span>
                </div>
              </div>
            </div>

            {/* Right Visual Column (Panchganga River Environmental Telemetry Preview) */}
            <div className="lg:col-span-5 animate-fade-in">
              <div className="relative mx-auto max-w-md lg:max-w-none">
                {/* Ambient Ripple Glow */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-blue-600/20 blur-xl animate-ripple-pulse" />

                <div className="relative rounded-2xl border border-cyan-500/30 bg-[#071e2b]/95 p-6 sm:p-7 shadow-2xl backdrop-blur-md space-y-5">
                  {/* Visual Header */}
                  <div className="flex items-center justify-between border-b border-cyan-900/60 pb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                        <Waves className="h-4 w-4 animate-float-slow" />
                      </div>
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block">
                          SURFACE WATER MONITORING
                        </span>
                        <h4 className="text-xs sm:text-sm font-bold text-white">
                          Panchganga River Basin &middot; Kolhapur
                        </h4>
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950/80 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-800/80">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Live Data
                    </span>
                  </div>

                  {/* Representative River Water Quality Telemetry */}
                  <div className="rounded-xl border border-cyan-800/40 bg-gradient-to-br from-[#0c2e42]/80 to-[#071e2b] p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-300">
                      <span className="font-semibold text-slate-200">Shivaji Bridge Monitoring Station</span>
                      <span className="font-mono text-[11px] text-cyan-300">16.7050°N, 74.2433°E</span>
                    </div>

                    <div className="flex items-baseline justify-between pt-1">
                      <div>
                        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                          Predicted WQI Assessment
                        </span>
                        <div className="flex items-baseline gap-2 mt-0.5">
                          <span className="text-2xl sm:text-3xl font-extrabold text-cyan-300">38.45</span>
                          <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">
                            Grade B &middot; Good Quality
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Parameter Pills Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[11px]">
                      <div className="rounded-lg bg-black/30 p-2 border border-cyan-900/50">
                        <span className="text-[10px] text-slate-400 block">pH Level</span>
                        <strong className="text-white">7.35</strong>
                      </div>
                      <div className="rounded-lg bg-black/30 p-2 border border-cyan-900/50">
                        <span className="text-[10px] text-slate-400 block">DO</span>
                        <strong className="text-white">6.90 mg/L</strong>
                      </div>
                      <div className="rounded-lg bg-black/30 p-2 border border-cyan-900/50">
                        <span className="text-[10px] text-slate-400 block">BOD</span>
                        <strong className="text-white">2.10 mg/L</strong>
                      </div>
                      <div className="rounded-lg bg-black/30 p-2 border border-cyan-900/50">
                        <span className="text-[10px] text-slate-400 block">Turbidity</span>
                        <strong className="text-white">3.80 NTU</strong>
                      </div>
                    </div>
                  </div>

                  {/* River Water Clarity Visual Indicator */}
                  <div className="rounded-lg bg-cyan-950/40 border border-cyan-800/30 p-3 space-y-1.5">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-300 font-medium flex items-center gap-1.5">
                        <Sparkles className="h-3 w-3 text-cyan-400" />
                        Clean River Resource Index
                      </span>
                      <span className="font-bold text-cyan-300">Optimal Range</span>
                    </div>
                    {/* Visual Progress Bar */}
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-gradient-to-r from-emerald-400 to-cyan-400 h-full w-[82%] rounded-full transition-all duration-1000" />
                    </div>
                  </div>

                  {/* Footnote on Visual */}
                  <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1">
                    <span className="flex items-center gap-1">
                      <Activity className="h-3.5 w-3.5 text-cyan-400" />
                      14 Laboratory Parameters
                    </span>
                    <span className="text-cyan-400 font-semibold">Maharashtra Network</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Container */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-16">
        {/* =================================================================== */}
        {/* SECTION 2: PLATFORM CAPABILITIES (ACTIONABLE USER-FACING CARDS)     */}
        {/* =================================================================== */}
        <Reveal>
          <section className="space-y-6">
            <div className="text-center max-w-2xl mx-auto space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean">
                EXPLORE FEATURES
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
                Platform Capabilities
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                Direct access to geospatial monitoring, automated machine learning assessment, and laboratory data tools.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {coreCapabilities.map((item, index) => {
                const Icon = item.icon
                return (
                  <Reveal key={item.title} delay={index * 90}>
                    <div className="group h-full rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs card-hover flex flex-col justify-between space-y-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div
                            className={`flex h-11 w-11 items-center justify-center rounded-xl border ${item.color} transition-transform group-hover:scale-105`}
                          >
                            <Icon className="h-5 w-5" />
                          </div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
                            {item.badge}
                          </span>
                        </div>

                        <h3 className="font-bold text-slate-900 text-lg group-hover:text-ocean transition-colors">
                          {item.title}
                        </h3>

                        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                          {item.description}
                        </p>
                      </div>

                      <div className="pt-2 border-t border-slate-100">
                        <Link
                          to={item.link}
                          className="inline-flex items-center gap-1.5 text-xs font-bold text-ocean hover:text-cyan-800 transition-colors group-hover:translate-x-1 transition-transform"
                        >
                          <span>{item.actionLabel}</span>
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </div>
                    </div>
                  </Reveal>
                )
              })}
            </div>
          </section>
        </Reveal>

        {/* =================================================================== */}
        {/* SECTION 3: SHORT VISUAL WORKFLOW (HOW IT WORKS PREVIEW)             */}
        {/* =================================================================== */}
        <Reveal>
          <section className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-10 shadow-xs space-y-8">
            <div className="text-center max-w-2xl mx-auto space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean">
                STREAMLINED WORKFLOW
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
                How It Works
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                A simple three-step journey transforming laboratory measurements into accessible environmental intelligence.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
              {quickWorkflow.map((item, idx) => {
                const Icon = item.icon
                return (
                  <div
                    key={item.step}
                    className="relative rounded-xl border border-slate-100 bg-slate-50/70 p-6 space-y-3.5 text-center flex flex-col items-center card-hover-subtle"
                  >
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white border-2 border-ocean text-ocean shadow-xs">
                      <Icon className="h-6 w-6" />
                    </div>

                    <span className="rounded bg-cyan-100/80 px-2 py-0.5 text-[10px] font-bold text-ocean uppercase tracking-wider">
                      Step {item.step}
                    </span>

                    <h4 className="font-bold text-slate-900 text-base">{item.title}</h4>

                    <p className="text-xs text-slate-600 leading-relaxed">{item.desc}</p>
                  </div>
                )
              })}
            </div>

            <div className="text-center pt-2">
              <Link
                to="/about#methodology"
                className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-ocean hover:text-cyan-800 transition-colors"
              >
                <span>Read detailed 14-parameter scientific methodology on the About page</span>
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </section>
        </Reveal>

        {/* =================================================================== */}
        {/* SECTION 4: ROLE-BASED ACCESS (PUBLIC vs LAB AUTHORITIES)            */}
        {/* =================================================================== */}
        <Reveal>
          <section className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-10 shadow-xs space-y-6">
            <div className="max-w-2xl space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean">
                PORTAL ACCESS
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
                Designed for the Public & Laboratory Authorities
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                Transparent environmental intelligence for citizens and researchers, alongside verified testing tools for laboratory personnel.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Public Access Card */}
              <div className="rounded-xl border border-cyan-100 bg-cyan-50/50 p-6 space-y-4 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-ocean">
                    <Compass className="h-5 w-5" />
                    <span className="text-xs font-bold uppercase tracking-wider">Public Visitors & Researchers</span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">
                    Open Environmental Information
                  </h3>
                  <ul className="space-y-2 text-xs text-slate-600">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                      <span>Browse state-wide GIS water quality map without an account</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                      <span>Inspect historical trends across key rivers and lakes</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                      <span>Understand standardized WQI scores and safety classifications</span>
                    </li>
                  </ul>
                </div>

                <div className="pt-3">
                  <Link
                    to="/map"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-white border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-50 transition-colors shadow-2xs"
                  >
                    <MapPin className="h-3.5 w-3.5 text-ocean" />
                    <span>Open Water Map</span>
                  </Link>
                </div>
              </div>

              {/* Lab Authority Access Card */}
              <div className="rounded-xl border border-blue-200 bg-blue-50/40 p-6 space-y-4 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-blue-900">
                    <ShieldCheck className="h-5 w-5 text-blue-700" />
                    <span className="text-xs font-bold uppercase tracking-wider">Certified Laboratories</span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">
                    Authorized Laboratory Portal
                  </h3>
                  <ul className="space-y-2 text-xs text-slate-600">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-blue-600 shrink-0" />
                      <span>Log authenticated 14-parameter water testing records</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-blue-600 shrink-0" />
                      <span>Generate official A4 downloadable laboratory test reports</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-blue-600 shrink-0" />
                      <span>Manage monitoring stations and maintain analytical audit trails</span>
                    </li>
                  </ul>
                </div>

                <div className="pt-3">
                  {isLabAuthority ? (
                    <Link
                      to="/dashboard"
                      className="inline-flex items-center gap-1.5 rounded-lg bg-ocean text-white px-4 py-2 text-xs font-semibold hover:bg-[#0c627a] transition-colors shadow-xs"
                    >
                      <FlaskConical className="h-3.5 w-3.5" />
                      <span>Go to Lab Dashboard</span>
                    </Link>
                  ) : (
                    <Link
                      to="/login"
                      className="inline-flex items-center gap-1.5 rounded-lg bg-ocean text-white px-4 py-2 text-xs font-semibold hover:bg-[#0c627a] transition-colors shadow-xs"
                    >
                      <FlaskConical className="h-3.5 w-3.5" />
                      <span>Lab Authority Login</span>
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </section>
        </Reveal>

        {/* =================================================================== */}
        {/* SECTION 5: CALL TO ACTION                                           */}
        {/* =================================================================== */}
        <Reveal>
          <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#071e2b] via-[#0b2a3a] to-[#071e2b] text-white p-8 sm:p-12 shadow-md border border-cyan-900/60 text-center space-y-6">
            <div className="absolute top-0 right-1/2 translate-x-1/2 w-80 h-32 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="max-w-3xl mx-auto space-y-3 relative z-10">
              <div className="inline-flex items-center gap-2 rounded-full bg-cyan-950 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-cyan-400 border border-cyan-800/60 mb-1">
                <Droplets className="h-3.5 w-3.5" />
                <span>Get Started</span>
              </div>

              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
                Explore Water Quality Information
              </h2>

              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Discover available monitoring locations, explore water quality results, and
                understand how technology can support water resource monitoring.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3.5 relative z-10 pt-2">
              <Link
                to="/map"
                className="btn-primary inline-flex items-center gap-2 text-xs sm:text-sm font-semibold px-5 py-3 shadow-md hover:shadow-lg transition-all active:scale-[0.98]"
              >
                <MapPin className="h-4 w-4" />
                <span>Explore Water Quality Map</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>

              <Link
                to="/about"
                className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-white/5 px-4 py-3 text-xs sm:text-sm font-semibold text-slate-200 hover:bg-white/10 hover:text-white transition-all active:scale-[0.98]"
              >
                <span>Learn More About AquaWatch AI</span>
                <ArrowRight className="h-3.5 w-3.5 text-cyan-400" />
              </Link>

              {isLabAuthority && (
                <Link
                  to="/test"
                  className="inline-flex items-center gap-2 rounded-lg border border-cyan-400/40 bg-cyan-950/60 px-4 py-3 text-xs sm:text-sm font-semibold text-cyan-300 hover:bg-cyan-900/60 transition-colors"
                >
                  <FlaskConical className="h-4 w-4" />
                  <span>Test Water Sample</span>
                </Link>
              )}
            </div>
          </section>
        </Reveal>
      </div>
    </div>
  )
}
