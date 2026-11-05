import { Link } from 'react-router-dom'
import {
  FlaskConical,
  Brain,
  MapPin,
  History,
  BarChart3,
  Globe,
  ShieldCheck,
  ArrowRight,
  Database,
  Layers,
  Code2,
  Server,
  Map as MapIcon,
  Palette,
  CheckCircle2,
  Sparkles,
  Droplets,
  Activity,
  Compass,
  Target,
  AlertTriangle,
  Scale,
  FileText,
  Cpu,
  BookOpen,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Reveal from '../components/Reveal'

export default function About() {
  const { user, isLabAuthority } = useAuth()

  // 6 Academic & Engineering Project Objectives
  const projectObjectives = [
    {
      icon: FlaskConical,
      title: 'Standardized Laboratory Data Management',
      description:
        'Establish an authenticated digital workflow for laboratory authorities to record and audit 14 physical, chemical, and biological water parameters.',
      color: 'text-cyan-700 bg-cyan-100/70 border-cyan-200',
    },
    {
      icon: Brain,
      title: 'Explainable Machine Learning Inference',
      description:
        'Deploy a trained DecisionTreeRegressor to calculate reproducible Water Quality Index (WQI) scores from 12 key environmental features.',
      color: 'text-indigo-700 bg-indigo-100/70 border-indigo-200',
    },
    {
      icon: MapPin,
      title: 'Spatial GIS Location Resolution',
      description:
        'Pin verified laboratory test results directly to geo-referenced coordinates across rivers, lakes, and reservoirs throughout Maharashtra.',
      color: 'text-emerald-700 bg-emerald-100/70 border-emerald-200',
    },
    {
      icon: History,
      title: 'Longitudinal Trend Analytics',
      description:
        'Retain historical observations in a relational database to examine chronological parameter shifts across dry and wet seasons.',
      color: 'text-amber-700 bg-amber-100/70 border-amber-200',
    },
    {
      icon: FileText,
      title: 'Certified PDF Report Generation',
      description:
        'Generate formal laboratory analysis documents adhering to official formatting with unique Sample IDs, technician credentials, and signature blocks.',
      color: 'text-blue-700 bg-blue-100/70 border-blue-200',
    },
    {
      icon: Globe,
      title: 'Open Environmental Accessibility',
      description:
        'Democratize access to water quality data for students, environmental researchers, and citizens without requiring sign-in credentials.',
      color: 'text-teal-700 bg-teal-100/70 border-teal-200',
    },
  ]

  // Actual Technology Stack Data
  const technologies = [
    {
      name: 'React.js',
      role: 'Frontend Development',
      description: 'Single-page application with responsive state management, client routing, and interactive telemetry views.',
      icon: Code2,
      tag: 'Frontend',
    },
    {
      name: 'FastAPI',
      role: 'Backend API Framework',
      description: 'Asynchronous Python REST framework delivering high-performance endpoints, Pydantic validation, and JWT auth.',
      icon: Server,
      tag: 'Backend',
    },
    {
      name: 'PostgreSQL',
      role: 'Relational Database',
      description: 'Structured database persistence for laboratories, users, water bodies, and immutable sampling records.',
      icon: Database,
      tag: 'Database',
    },
    {
      name: 'Python',
      role: 'Backend & ML Runtime',
      description: 'Underlying programming language powering scientific calculation, data modeling, and API services.',
      icon: Layers,
      tag: 'Language',
    },
    {
      name: 'Scikit-learn',
      role: 'Machine Learning Model',
      description: 'Trained DecisionTreeRegressor artifact evaluating 12 features to predict standardized WQI scores.',
      icon: Brain,
      tag: 'Machine Learning',
    },
    {
      name: 'SQLAlchemy',
      role: 'Database ORM',
      description: 'Object Relational Mapper managing schema relations, migrations, transactions, and foreign key integrity.',
      icon: Database,
      tag: 'ORM',
    },
    {
      name: 'Leaflet & OpenStreetMap',
      role: 'Geospatial Mapping',
      description: 'Interactive map layer bounded to Maharashtra with localized place search and marker cluster navigation.',
      icon: MapIcon,
      tag: 'Geospatial',
    },
    {
      name: 'Tailwind CSS',
      role: 'Styling & Design System',
      description: 'Utility-first modern styling framework providing clean typography, water-inspired palette, and smooth transitions.',
      icon: Palette,
      tag: 'Design System',
    },
  ]

  // Project Scope & Limitations
  const scopeAndLimitations = [
    {
      title: 'Geographic Scope: Maharashtra, India',
      description:
        'The platform spatial map and monitoring station directory are currently bounded to Maharashtra (Krishna, Godavari, and Panchganga basins).',
      badge: 'Geographic Boundary',
      icon: Compass,
      color: 'border-cyan-200 bg-cyan-50/60 text-cyan-900',
    },
    {
      title: 'Laboratory Testing Input Requirement',
      description:
        'AquaWatch AI processes authenticated laboratory measurements. It does not replace physical laboratory assays or operate real-time in-situ IoT probes.',
      badge: 'Data Dependency',
      icon: FlaskConical,
      color: 'border-blue-200 bg-blue-50/60 text-blue-900',
    },
    {
      title: 'Predictive Screening & Classification',
      description:
        'The machine learning model generates an indicative Water Quality Index (WQI) score for preliminary screening. It does not constitute a statutory regulatory certification.',
      badge: 'Model Scope',
      icon: Scale,
      color: 'border-indigo-200 bg-indigo-50/60 text-indigo-900',
    },
    {
      title: 'Academic & Applied Engineering Prototype',
      description:
        'Developed as an advanced computer science and environmental engineering project demonstrating the integration of full-stack development, GIS, and machine learning.',
      badge: 'Project Context',
      icon: BookOpen,
      color: 'border-emerald-200 bg-emerald-50/60 text-emerald-900',
    },
  ]

  return (
    <div className="min-h-screen bg-mist text-ink antialiased selection:bg-cyan-100 selection:text-ocean space-y-16 pb-16">
      {/* ========================================================= */}
      {/* SECTION 1: HERO (PROJECT OVERVIEW & SYSTEM ARCHITECTURE)  */}
      {/* ========================================================= */}
      <section className="relative overflow-hidden bg-gradient-to-b from-[#071e2b] via-[#0b2a3a] to-[#071e2b] text-white pt-16 pb-20 sm:pt-20 sm:pb-24 px-4 sm:px-6 lg:px-8 border-b border-cyan-900/40">
        {/* Subtle Water Light/Grid Effects */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900/25 via-transparent to-transparent pointer-events-none" />
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 rounded-full bg-ocean/10 blur-3xl pointer-events-none" />

        <div className="relative mx-auto max-w-7xl">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            {/* Left Content Column */}
            <div className="lg:col-span-7 space-y-5 animate-fade-slide-up">
              <div className="inline-flex items-center gap-2 rounded-full bg-cyan-950/80 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-cyan-300 border border-cyan-700/60 shadow-xs">
                <BookOpen className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                <span>Project Documentation & Scientific Reference</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight">
                About AquaWatch AI
              </h1>

              <h2 className="text-lg sm:text-xl font-bold text-cyan-300 leading-snug">
                Scientific Background, Machine Learning Architecture & Project Scope
              </h2>

              <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
                AquaWatch AI is an environmental engineering and data intelligence project developed
                to modernize surface water quality monitoring. By bridging validated multi-parameter
                laboratory analysis with trained machine learning regression and interactive GIS mapping,
                the platform provides explainable, reproducible Water Quality Index (WQI) assessments
                across monitored water bodies.
              </p>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-wrap items-center gap-3.5">
                <a
                  href="#problem-statement"
                  className="btn-primary inline-flex items-center gap-2 text-xs sm:text-sm font-semibold px-5 py-2.5 shadow-md transition-all hover:shadow-lg hover:bg-[#0c627a] active:scale-[0.98]"
                >
                  <Target className="h-4 w-4" />
                  <span>Problem Statement & Motivation</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </a>

                <a
                  href="#methodology"
                  className="inline-flex items-center gap-1.5 rounded-md border border-slate-600 bg-white/5 px-4 py-2.5 text-xs sm:text-sm font-semibold text-slate-200 hover:bg-white/10 hover:text-white transition-colors"
                >
                  <span>Data Pipeline & Methodology</span>
                  <Layers className="h-3.5 w-3.5 text-cyan-400" />
                </a>
              </div>

              {/* Technical Badges */}
              <div className="pt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 border-t border-cyan-900/60 text-xs text-slate-300">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>CPCB & BIS IS 10500 Standards</span>
                </div>
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>DecisionTreeRegressor (12 Features)</span>
                </div>
                <div className="flex items-center gap-2 col-span-2 sm:col-span-1">
                  <Database className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span>PostgreSQL Relational Storage</span>
                </div>
              </div>
            </div>

            {/* Right Visual Column (Dedicated System Architecture Blueprint Card) */}
            <div className="lg:col-span-5 animate-fade-in">
              <div className="relative mx-auto max-w-md lg:max-w-none">
                <div className="relative rounded-2xl border border-cyan-500/30 bg-[#071e2b]/95 p-6 shadow-2xl backdrop-blur-md space-y-4">
                  <div className="flex items-center justify-between border-b border-cyan-900/60 pb-3">
                    <div className="flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-cyan-400" />
                      <span className="text-xs font-bold uppercase tracking-wider text-white">
                        System Architecture Blueprint
                      </span>
                    </div>
                    <span className="text-[10px] font-bold text-cyan-300 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                      Pipeline
                    </span>
                  </div>

                  {/* Visual Architecture Layers */}
                  <div className="space-y-2.5 text-xs">
                    {/* Layer 1: Data Ingestion */}
                    <div className="rounded-lg bg-black/40 border border-cyan-900/60 p-2.5 flex items-start gap-2.5">
                      <div className="flex h-6 w-6 items-center justify-center rounded bg-cyan-500/20 text-cyan-400 shrink-0 font-bold text-[10px]">
                        01
                      </div>
                      <div>
                        <strong className="text-white block text-[11.5px]">Laboratory Input Layer</strong>
                        <span className="text-slate-400 text-[11px]">
                          14 Physical, chemical & microbial parameters validated against NABL / CPCB limits.
                        </span>
                      </div>
                    </div>

                    {/* Layer 2: Feature Transformation */}
                    <div className="rounded-lg bg-black/40 border border-cyan-900/60 p-2.5 flex items-start gap-2.5">
                      <div className="flex h-6 w-6 items-center justify-center rounded bg-indigo-500/20 text-indigo-400 shrink-0 font-bold text-[10px]">
                        02
                      </div>
                      <div>
                        <strong className="text-white block text-[11.5px]">Model Feature Vector</strong>
                        <span className="text-slate-400 text-[11px]">
                          12 ML features extracted & scaled for model compatibility: pH, DO, BOD, COD, Turbidity, TDS, Temp, Nitrate, etc.
                        </span>
                      </div>
                    </div>

                    {/* Layer 3: ML Inference */}
                    <div className="rounded-lg bg-black/40 border border-cyan-900/60 p-2.5 flex items-start gap-2.5">
                      <div className="flex h-6 w-6 items-center justify-center rounded bg-purple-500/20 text-purple-400 shrink-0 font-bold text-[10px]">
                        03
                      </div>
                      <div>
                        <strong className="text-white block text-[11.5px]">Decision Tree Regression</strong>
                        <span className="text-slate-400 text-[11px]">
                          Continuous WQI score (0–100) computation with standardized safety classification (Grade A to E).
                        </span>
                      </div>
                    </div>

                    {/* Layer 4: Persistence & GIS */}
                    <div className="rounded-lg bg-black/40 border border-cyan-900/60 p-2.5 flex items-start gap-2.5">
                      <div className="flex h-6 w-6 items-center justify-center rounded bg-emerald-500/20 text-emerald-400 shrink-0 font-bold text-[10px]">
                        04
                      </div>
                      <div>
                        <strong className="text-white block text-[11.5px]">Persistence & Spatial Presentation</strong>
                        <span className="text-slate-400 text-[11px]">
                          PostgreSQL audit storage, A4 certified PDF generation, and Leaflet GIS mapping.
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-1 flex items-center justify-between text-[11px] text-slate-400 border-t border-cyan-900/60">
                    <span>Artifact: AquaWatchAI_Best_Model.joblib</span>
                    <span className="text-cyan-400 font-semibold">FastAPI + PostgreSQL</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Container */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-16">
        {/* ========================================================= */}
        {/* SECTION 2: PROBLEM STATEMENT & MOTIVATION                */}
        {/* ========================================================= */}
        <Reveal>
          <section id="problem-statement" className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-10 shadow-xs space-y-6 scroll-mt-20">
            <div className="max-w-3xl space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean flex items-center gap-1.5">
                <Target className="h-3.5 w-3.5" />
                <span>Context & Justification</span>
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
                Problem Statement & Project Motivation
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                Why modern software engineering and machine learning are necessary for surface water quality management.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-600 text-sm leading-relaxed">
              <div className="rounded-xl border border-rose-100 bg-rose-50/40 p-5 space-y-3">
                <div className="flex items-center gap-2 text-rose-900 font-bold text-base">
                  <AlertTriangle className="h-5 w-5 text-rose-600" />
                  <span>Challenges in Conventional Monitoring</span>
                </div>
                <p>
                  Water testing records are frequently archived across fragmented spreadsheets, physical logbooks,
                  and isolated laboratory reports. Calculating comprehensive Water Quality Indices (WQI) manually
                  is mathematically complex and time-consuming, delaying critical environmental advisories.
                </p>
                <p>
                  Furthermore, public access to river basin condition data remains limited, making it difficult for
                  researchers and communities to monitor seasonal pollution dynamics or identify contamination hotspots.
                </p>
              </div>

              <div className="rounded-xl border border-cyan-100 bg-cyan-50/40 p-5 space-y-3">
                <div className="flex items-center gap-2 text-ocean font-bold text-base">
                  <Sparkles className="h-5 w-5 text-ocean" />
                  <span>The AquaWatch AI Solution</span>
                </div>
                <p>
                  AquaWatch AI addresses these challenges by offering a centralized, validated platform where
                  laboratory technicians record multi-parameter water tests that are instantly evaluated by an
                  AI regression pipeline.
                </p>
                <p>
                  Results are immediately geo-referenced on an open GIS map, tracked across historical timelines, and
                  rendered into verifiable PDF certificates, transforming static data into accessible environmental intelligence.
                </p>
              </div>
            </div>
          </section>
        </Reveal>

        {/* ========================================================= */}
        {/* SECTION 3: MISSION & VISION                               */}
        {/* ========================================================= */}
        <Reveal>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
            {/* Mission Card */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-7 sm:p-9 shadow-xs hover:shadow-md transition-all duration-300 hover:-translate-y-1 space-y-4 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-28 h-28 bg-ocean/5 rounded-bl-full pointer-events-none transition-transform group-hover:scale-110" />
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-100/80 text-ocean">
                <Target className="h-6 w-6" />
              </div>
              <h3 className="text-xl sm:text-2xl font-extrabold text-ink tracking-tight">
                Our Mission
              </h3>
              <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
                To provide environmental authorities, accredited laboratories, and researchers with an
                organized, open platform for rigorous water quality data management, explainable machine
                learning assessment, and spatial watershed monitoring.
              </p>
            </div>

            {/* Vision Card */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-7 sm:p-9 shadow-xs hover:shadow-md transition-all duration-300 hover:-translate-y-1 space-y-4 relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-28 h-28 bg-emerald-500/5 rounded-bl-full pointer-events-none transition-transform group-hover:scale-110" />
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100/80 text-emerald-600">
                <Compass className="h-6 w-6" />
              </div>
              <h3 className="text-xl sm:text-2xl font-extrabold text-ink tracking-tight">
                Our Vision
              </h3>
              <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
                To support sustainable water resource stewardship and pollution mitigation through
                accessible data, scientific transparency, and intelligent environmental technology.
              </p>
            </div>
          </div>
        </Reveal>

        {/* ========================================================= */}
        {/* SECTION 4: PROJECT OBJECTIVES                             */}
        {/* ========================================================= */}
        <Reveal>
          <section className="space-y-6">
            <div className="text-center max-w-2xl mx-auto space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean">
                SYSTEM OBJECTIVES
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
                Key Project Objectives
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                Academic and engineering goals guiding the development of AquaWatch AI.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {projectObjectives.map((obj) => {
                const Icon = obj.icon
                return (
                  <div
                    key={obj.title}
                    className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-xs card-hover space-y-3.5 group"
                  >
                    <div
                      className={`flex h-11 w-11 items-center justify-center rounded-xl border ${obj.color} transition-transform group-hover:scale-105`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="font-bold text-slate-900 text-base">{obj.title}</h3>
                    <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                      {obj.description}
                    </p>
                  </div>
                )
              })}
            </div>
          </section>
        </Reveal>

        {/* ========================================================= */}
        {/* SECTION 5: DETAILED METHODOLOGY & DATA PIPELINE           */}
        {/* ========================================================= */}
        <Reveal>
          <section id="methodology" className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-10 shadow-xs space-y-8 scroll-mt-20">
            <div className="max-w-3xl space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5" />
                <span>Scientific Methodology</span>
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
                Data Pipeline & Analytical Methodology
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                Understanding how 14 laboratory measurements are processed, validated, and evaluated by the ML model.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Pillar 1 */}
              <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-5 space-y-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-100 text-ocean font-bold text-xs">
                  01
                </div>
                <h3 className="font-bold text-slate-900 text-base">14 Laboratory Parameters</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Laboratory technicians enter 14 parameters: pH, Dissolved Oxygen (DO), BOD, COD, Turbidity,
                  TDS, Electrical Conductivity, Temperature, Nitrate, Phosphate, Chloride, Total Coliform,
                  Fecal Coliform, and Sulphate or Ammonia-N.
                </p>
                <div className="pt-1 text-[11px] font-semibold text-ocean">
                  Complies with CPCB & IS 10500 Protocols
                </div>
              </div>

              {/* Pillar 2 */}
              <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-5 space-y-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700 font-bold text-xs">
                  02
                </div>
                <h3 className="font-bold text-slate-900 text-base">12 ML Feature Alignment</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  The trained Decision Tree artifact requires exactly 12 specific features. The FastAPI backend
                  validates input boundaries, applies baseline sanity checks, and constructs the feature vector
                  for instantaneous deterministic inference.
                </p>
                <div className="pt-1 text-[11px] font-semibold text-indigo-700">
                  Model: DecisionTreeRegressor (scikit-learn)
                </div>
              </div>

              {/* Pillar 3 */}
              <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-5 space-y-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700 font-bold text-xs">
                  03
                </div>
                <h3 className="font-bold text-slate-900 text-base">WQI Scoring & Standardized Grades</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  The predicted WQI is translated into standardized environmental quality grades:
                  <strong> Grade A (Excellent: WQI &lt; 25)</strong>, 
                  <strong> Grade B (Good: 26–50)</strong>, 
                  <strong> Grade C (Poor: 51–75)</strong>, 
                  <strong> Grade D (Very Poor: 76–100)</strong>, and 
                  <strong> Grade E (Unfit: &gt; 100)</strong>.
                </p>
                <div className="pt-1 text-[11px] font-semibold text-emerald-700">
                  Deterministic & Reproducible Classification
                </div>
              </div>
            </div>
          </section>
        </Reveal>

        {/* ========================================================= */}
        {/* SECTION 6: TECHNOLOGY STACK                               */}
        {/* ========================================================= */}
        <Reveal>
          <section className="space-y-6">
            <div className="text-center max-w-2xl mx-auto space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean">
                SYSTEM ARCHITECTURE
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
                Technology Stack
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                Core technologies and frameworks actively implemented in the existing AquaWatch AI project codebase.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {technologies.map((tech) => {
                const Icon = tech.icon
                return (
                  <div
                    key={tech.name}
                    className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-xs card-hover space-y-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-50 border border-cyan-100 text-ocean">
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                        {tech.tag}
                      </span>
                    </div>

                    <div>
                      <h3 className="font-bold text-slate-900 text-base">{tech.name}</h3>
                      <p className="text-xs font-semibold text-ocean">{tech.role}</p>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">{tech.description}</p>
                  </div>
                )
              })}
            </div>
          </section>
        </Reveal>

        {/* ========================================================= */}
        {/* SECTION 7: PROJECT SCOPE & LIMITATIONS                    */}
        {/* ========================================================= */}
        <Reveal>
          <section className="rounded-2xl border border-slate-200/80 bg-white p-6 sm:p-10 shadow-xs space-y-6">
            <div className="max-w-3xl space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ocean flex items-center gap-1.5">
                <Scale className="h-3.5 w-3.5" />
                <span>Transparency & Ethics</span>
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
                Project Scope and Limitations
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                Explicit boundaries and operational context to ensure scientific accuracy without inflated claims.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {scopeAndLimitations.map((item) => {
                const Icon = item.icon
                return (
                  <div
                    key={item.title}
                    className={`rounded-xl border p-5 space-y-2.5 ${item.color} card-hover-subtle`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-bold text-sm">
                        <Icon className="h-4 w-4 shrink-0" />
                        <span>{item.title}</span>
                      </div>
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-white/70 border border-current">
                        {item.badge}
                      </span>
                    </div>
                    <p className="text-xs leading-relaxed text-slate-700">
                      {item.description}
                    </p>
                  </div>
                )
              })}
            </div>
          </section>
        </Reveal>

        {/* ========================================================= */}
        {/* SECTION 8: EXPLORE NEXT / CALL TO ACTION                  */}
        {/* ========================================================= */}
        <Reveal>
          <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#071e2b] via-[#0b2a3a] to-[#071e2b] text-white p-8 sm:p-12 shadow-md border border-cyan-900/60 text-center space-y-6">
            <div className="absolute top-0 right-1/2 translate-x-1/2 w-80 h-32 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="max-w-3xl mx-auto space-y-3 relative z-10">
              <div className="inline-flex items-center gap-2 rounded-full bg-cyan-950 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-cyan-400 border border-cyan-800/60 mb-1">
                <Droplets className="h-3.5 w-3.5" />
                <span>Interactive Exploration</span>
              </div>

              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
                Ready to Explore the Platform?
              </h2>

              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Experience the interactive water monitoring map, inspect longitudinal station trends,
                or access the authenticated laboratory portal.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3.5 relative z-10 pt-2">
              <Link
                to="/map"
                className="btn-primary inline-flex items-center gap-2 text-xs sm:text-sm font-semibold px-5 py-2.5 shadow-md transition-all hover:bg-[#0c627a] active:scale-[0.98]"
              >
                <MapPin className="h-4 w-4" />
                <span>Explore Water Quality Map</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>

              <Link
                to="/intelligence"
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 bg-white/5 px-4 py-2.5 text-xs sm:text-sm font-semibold text-slate-200 hover:bg-white/10 hover:text-white transition-colors"
              >
                <Activity className="h-4 w-4 text-cyan-400" />
                <span>View Water Quality Intelligence</span>
              </Link>

              {isLabAuthority ? (
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-2 rounded-md border border-cyan-400/40 bg-cyan-950/60 px-4 py-2.5 text-xs sm:text-sm font-semibold text-cyan-300 hover:bg-cyan-900/60 transition-colors"
                >
                  <FlaskConical className="h-4 w-4" />
                  <span>Lab Dashboard</span>
                </Link>
              ) : (
                <Link
                  to="/login"
                  className="inline-flex items-center gap-2 rounded-md border border-slate-600 bg-white/5 px-4 py-2.5 text-xs sm:text-sm font-semibold text-slate-200 hover:bg-white/10 hover:text-white transition-colors"
                >
                  <FlaskConical className="h-4 w-4 text-cyan-400" />
                  <span>Laboratory Login</span>
                </Link>
              )}
            </div>
          </section>
        </Reveal>
      </div>
    </div>
  )
}
