import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import ChartCard from './ChartCard'

export default function ImportanceChart({ data, title = 'Why this WQI?' }) {
  return (
    <ChartCard title={title} subtitle="Model Feature Importance (mock values, not scientifically validated)">
      <div className="h-56">
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
            <XAxis type="number" unit="%" domain={[0, 40]} fontSize={12} />
            <YAxis type="category" dataKey="name" width={70} fontSize={12} />
            <Tooltip formatter={(v) => `${v}%`} />
            <Bar dataKey="value" fill="#0e7490" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  )
}
