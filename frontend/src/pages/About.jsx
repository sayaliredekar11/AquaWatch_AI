import {
  Database,
  CheckCircle2,
  Filter,
  GitFork,
  Brain,
  BarChart3,
  Scale,
  Activity,
  Sparkles,
  Target,
  Map,
  ArrowRight,
} from 'lucide-react'

const pipelineSteps = [
  { num: '01', title: 'Historical Dataset', icon: Database },
  { num: '02', title: 'Data Cleaning', icon: CheckCircle2 },
  { num: '03', title: 'Feature Selection', icon: Filter },
  { num: '04', title: 'Train / Test Split', icon: GitFork },
  { num: '05', title: 'Model Training', icon: Brain },
  { num: '06', title: 'Model Evaluation', icon: BarChart3 },
  { num: '07', title: 'Best Model', icon: Scale },
  { num: '08', title: 'WQI Prediction', icon: Activity },
  { num: '09', title: 'Explainability', icon: Sparkles },
  { num: '10', title: 'Anomaly Detection', icon: Target },
  { num: '11', title: 'GIS Visualization', icon: Map },
]

const candidateModels = [
  'Linear Regression',
  'Random Forest Regressor',
  'Gradient Boosting / XGBoost',
]

const parameters = [
  { name: 'pH', unit: 'Dimensionless' },
  { name: 'Dissolved Oxygen', unit: 'mg/L' },
  { name: 'BOD', unit: 'mg/L' },
  { name: 'COD', unit: 'mg/L' },
  { name: 'TDS', unit: 'mg/L' },
  { name: 'Turbidity', unit: 'NTU' },
  { name: 'Temperature', unit: '°C' },
  { name: 'Nitrate', unit: 'mg/L' },
  { name: 'Phosphate', unit: 'mg/L' },
]

const techStack = [
  {
    category: 'Frontend',
    items: ['ReactJS', 'Tailwind CSS', 'Recharts', 'Leaflet + OpenStreetMap'],
  },
  {
    category: 'Backend',
    items: ['FastAPI (Planned API Endpoint)'],
  },
  {
    category: 'Machine Learning',
    items: ['Python', 'Pandas', 'NumPy', 'scikit-learn'],
  },
  {
    category: 'Data / Storage',
    items: ['PostgreSQL (Planned)', 'PostGIS (Planned)'],
  },
  {
    category: 'Model Storage',
    items: ['Pre-trained regression model', 'Joblib / Pickle'],
  },
]

const archFlow = [
  'Laboratory Measurements',
  'Data Validation',
  'Preprocessing',
  'Trained ML Model',
  'WQI Prediction',
  'FastAPI Endpoint',
  'React Dashboard',
]

export default function About() {
  return (
    <div className="space-y-10 pb-12">
      {/* 1. HERO SECTION */}
      <section className="bg-ink text-white py-14 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 block mb-2">
            TRANSPARENT METHODOLOGY
          </span>
          <h1 className="text-3xl font-extrabold sm:text-4xl text-white tracking-tight leading-tight">
            How measurements become <br className="hidden sm:inline" />
            water intelligence
          </h1>
          <p className="mt-4 max-w-3xl text-slate-300 text-sm sm:text-base leading-relaxed">
            AquaWatch AI combines laboratory validation, machine learning, explainability,
            historical context, and geographic visualization to turn water-quality measurements
            into actionable insights.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-12">
        {/* 2. WHAT IS AQUAWATCH AI? */}
        <section className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm">
          <h2 className="text-2xl font-bold text-ink mb-3">What is AquaWatch AI?</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-slate-600 text-sm sm:text-base leading-relaxed">
            <p>
              AquaWatch AI is a water-quality intelligence platform that transforms
              laboratory-measured water parameters into an explainable Water Quality Index
              (WQI), historical insights, anomaly indicators, and location-based visualizations.
            </p>
            <p className="border-l-2 border-ocean/40 pl-4 italic text-slate-700 font-medium">
              "The system is designed to connect reliable laboratory measurements with
              machine-learning-based assessment while keeping the analysis transparent and
              traceable."
            </p>
          </div>
        </section>

        {/* 3. TECHNICAL PIPELINE */}
        <section className="space-y-4">
          <div>
            <h2 className="text-2xl font-bold text-ink">Technical Pipeline</h2>
            <p className="text-sm text-slate-600 mt-1">
              Each stage is designed to preserve traceability from source measurement to
              interpreted result.
            </p>
          </div>

          <div className="overflow-x-auto pb-4">
            <div className="flex items-center gap-3 min-w-max">
              {pipelineSteps.map((step, idx) => {
                const Icon = step.icon
                return (
                  <div key={step.num} className="flex items-center gap-3">
                    <div className="w-40 rounded-xl border border-slate-200/80 bg-white p-4 shadow-sm flex flex-col justify-between h-28 hover:shadow-md transition-shadow">
                      <Icon className="h-5 w-5 text-ocean" />
                      <div>
                        <span className="text-xs font-semibold text-slate-400 block mb-0.5">
                          {step.num}
                        </span>
                        <h3 className="text-xs font-bold text-slate-900 leading-tight">
                          {step.title}
                        </h3>
                      </div>
                    </div>
                    {idx < pipelineSteps.length - 1 && (
                      <ArrowRight className="h-4 w-4 text-cyan-400 shrink-0" />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        {/* 4 & 5. CANDIDATE MODELS & EVALUATION */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Candidate ML Models */}
          <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-sm flex flex-col justify-between space-y-4">
            <div>
              <h2 className="text-xl font-bold text-ink">Candidate ML Models</h2>
              <p className="text-xs sm:text-sm text-slate-600 mt-1 leading-relaxed">
                The system evaluates multiple regression approaches and selects the final model using
                performance on held-out test data rather than assuming a particular algorithm will perform best.
              </p>
            </div>

            <div className="space-y-2.5">
              {candidateModels.map((model) => (
                <div
                  key={model}
                  className="flex items-center gap-3 rounded-lg bg-cyan-50/60 border border-cyan-100 px-4 py-3 text-sm font-semibold text-slate-800"
                >
                  <Brain className="h-4 w-4 text-ocean shrink-0" />
                  <span>{model}</span>
                </div>
              ))}
            </div>

            <p className="text-xs text-slate-500 italic">
              Note: The final trained model will be selected after evaluation on held-out test data.
            </p>
          </div>

          {/* Model Evaluation & Selection */}
          <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-sm flex flex-col justify-between space-y-4">
            <div>
              <h2 className="text-xl font-bold text-ink">Evaluation & Selection</h2>
              <p className="text-xs sm:text-sm text-slate-600 mt-1 leading-relaxed">
                The final model should be selected from held-out test performance, consistency,
                and interpretability — not by model name.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-3 text-center">
                <span className="text-lg font-bold text-ocean block">MAE</span>
                <span className="text-[11px] text-slate-500 font-medium block mt-0.5">
                  Mean absolute error
                </span>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-3 text-center">
                <span className="text-lg font-bold text-ocean block">RMSE</span>
                <span className="text-[11px] text-slate-500 font-medium block mt-0.5">
                  Root mean square error
                </span>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-3 text-center">
                <span className="text-lg font-bold text-ocean block">R²</span>
                <span className="text-[11px] text-slate-500 font-medium block mt-0.5">
                  Explained variance
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Lower MAE and RMSE indicate smaller prediction errors, while a higher R² indicates that
              the model explains more variation in the target.
            </p>
          </div>
        </section>

        {/* 8. EXPLAINABILITY NOTE */}
        <section className="rounded-xl bg-[#e0f2fe]/80 border-l-4 border-ocean p-5 text-slate-800 space-y-1 shadow-xs">
          <h3 className="font-bold text-ink text-base">Interpretation, not causation</h3>
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
            Model feature importance indicates which input variables the model relied on more
            strongly when producing a prediction. It does not scientifically prove that a
            parameter caused the measured water condition.
          </p>
        </section>

        {/* 6. DATA -> MODEL -> APPLICATION ARCHITECTURE */}
        <section className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-ink">From trained model to application</h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl leading-relaxed">
              The machine-learning model is developed separately in Python and will be exposed
              through a FastAPI endpoint. The React frontend sends validated water-quality
              parameters to the API and displays the returned WQI and model interpretation.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 pt-2">
            {archFlow.map((node, i) => (
              <div key={node} className="flex items-center gap-2 sm:gap-3">
                <div className="rounded-lg border border-cyan-200 bg-cyan-50/80 px-3.5 py-2 text-xs sm:text-sm font-semibold text-slate-800 shadow-xs">
                  {node}
                </div>
                {i < archFlow.length - 1 && (
                  <ArrowRight className="h-4 w-4 text-slate-400 shrink-0 hidden sm:inline-block" />
                )}
              </div>
            ))}
          </div>
        </section>

        {/* 7. WATER PARAMETERS */}
        <section className="space-y-4">
          <div>
            <h2 className="text-2xl font-bold text-ink">Parameters used for assessment</h2>
            <p className="text-sm text-slate-600 mt-1">
              Key physical and chemical water-quality indicators evaluated by the model.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-9 gap-3">
            {parameters.map((p) => (
              <div
                key={p.name}
                className="rounded-xl border border-slate-200/80 bg-white p-3 text-center shadow-xs"
              >
                <p className="text-sm font-bold text-slate-900">{p.name}</p>
                <p className="text-[10px] font-medium text-slate-500 mt-0.5">{p.unit}</p>
              </div>
            ))}
          </div>
        </section>

        {/* 9. TECHNOLOGY STACK */}
        <section className="rounded-xl border border-slate-200/80 bg-white p-6 sm:p-8 shadow-sm space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-ink">Technology Stack</h2>
            <p className="text-sm text-slate-600 mt-1">
              Core frameworks and libraries powering the AquaWatch AI platform.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {techStack.map((group) => (
              <div
                key={group.category}
                className="rounded-lg border border-slate-100 bg-slate-50/50 p-4 space-y-2.5"
              >
                <h3 className="text-xs font-bold uppercase tracking-wider text-ocean">
                  {group.category}
                </h3>
                <ul className="space-y-1.5">
                  {group.items.map((item) => (
                    <li key={item} className="flex items-center gap-2 text-xs sm:text-sm font-medium text-slate-700">
                      <span className="h-1.5 w-1.5 rounded-full bg-cyan-600" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

