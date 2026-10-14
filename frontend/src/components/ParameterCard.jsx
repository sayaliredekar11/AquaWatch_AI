export default function ParameterCard({ label, value, unit }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold">{value} <span className="text-xs font-normal text-slate-500">{unit}</span></p>
    </div>
  )
}
