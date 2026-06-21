import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import ChartCard from '../components/ChartCard'
import SectionTitle from '../components/SectionTitle'
import { ErrorState, LoadingState } from '../components/QueryState'
import { formatNumber } from '../components/chartTheme'

const clusterColors = {
  'High Traffic — Reliable': '#34d399',
  'High Traffic — Delay Prone': '#f97316',
  'Low Traffic — Reliable': '#38bdf8',
  'Low Traffic — Delay Prone': '#ef4444',
}

export default function MLPage() {
  const [showAll, setShowAll] = useState(false)
  const anomalies = useQuery({ queryKey: ['anomalies'], queryFn: api.anomalies })
  const stops = useQuery({ queryKey: ['stop-clusters'], queryFn: api.stopClusters })
  const profiles = useQuery({ queryKey: ['cluster-profiles'], queryFn: api.clusterProfiles })
  const queries = [anomalies, stops, profiles]
  const error = queries.find((query) => query.isError)?.error
  if (error) return <ErrorState error={error} />
  if (queries.some((query) => query.isLoading)) return <LoadingState className="h-80" />

  const sortedAnomalies = [...anomalies.data].sort((a, b) => b.anomaly_score - a.anomaly_score).slice(0, 20)
  const sortedStops = [...stops.data].sort((a, b) => a.cluster_label.localeCompare(b.cluster_label) || b.total_passengers - a.total_passengers)
  const visibleStops = showAll ? sortedStops : sortedStops.slice(0, 50)

  return (
    <div className="space-y-8">
      <section className="space-y-5">
        <SectionTitle>Ridership Anomaly Detection</SectionTitle>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {profiles.data.map((profile) => {
            const color = clusterColors[profile.cluster_label] || '#94a3b8'
            return (
              <div key={profile.cluster_label} className="rounded-2xl border bg-[#0f172a] p-5" style={{ borderColor: color }}>
                <h3 className="min-h-12 font-semibold text-slate-100">{profile.cluster_label}</h3>
                <div className="mt-3 text-2xl font-bold" style={{ color }}>{formatNumber(profile.stop_count)} stops</div>
                <div className="mt-3 text-sm text-slate-400">Avg passengers: <span className="text-slate-200">{formatNumber(Math.round(profile.avg_passengers))}</span></div>
                <div className="mt-1 text-sm text-slate-400">Avg delay: <span className="text-slate-200">{Number(profile.avg_delay).toFixed(2)} min</span></div>
              </div>
            )
          })}
        </div>
        <ChartCard title="Top Anomalous Days">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-400"><tr><th className="px-4 py-3">Date</th><th className="px-4 py-3">Passengers</th><th className="px-4 py-3">Avg Delay (min)</th><th className="px-4 py-3">Anomaly Score</th></tr></thead>
              <tbody>
                {sortedAnomalies.map((row, index) => (
                  <tr key={row.full_date} className={index % 2 ? 'bg-slate-900/45' : 'bg-slate-800/20'}>
                    <td className="px-4 py-3">{row.full_date}</td><td className="px-4 py-3 text-slate-400">{formatNumber(row.total_passengers)}</td><td className="px-4 py-3 text-slate-400">{Number(row.avg_delay).toFixed(2)}</td><td className="px-4 py-3 font-semibold text-red-400">{Number(row.anomaly_score).toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ChartCard>
      </section>

      <section className="space-y-5">
        <SectionTitle>Stop Cluster Analysis</SectionTitle>
        <ChartCard title="Stops by Cluster">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-400"><tr><th className="px-4 py-3">Stop Name</th><th className="px-4 py-3">Cluster</th><th className="px-4 py-3">Total Passengers</th><th className="px-4 py-3">Avg Delay</th></tr></thead>
              <tbody>
                {visibleStops.map((row, index) => {
                  const color = clusterColors[row.cluster_label] || '#94a3b8'
                  return (
                    <tr key={row.stop_id} className={index % 2 ? 'bg-slate-900/45' : 'bg-slate-800/20'}>
                      <td className="px-4 py-3 text-slate-200">{row.stop_name}</td>
                      <td className="px-4 py-3"><span className="inline-flex rounded-full border px-2.5 py-1 text-xs" style={{ color, borderColor: `${color}88`, backgroundColor: `${color}18` }}>{row.cluster_label}</span></td>
                      <td className="px-4 py-3 text-slate-400">{formatNumber(row.total_passengers)}</td>
                      <td className="px-4 py-3 text-slate-400">{Number(row.avg_delay).toFixed(2)} min</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {!showAll && sortedStops.length > 50 && <button type="button" onClick={() => setShowAll(true)} className="mt-5 rounded-lg border border-brand/50 px-4 py-2 text-sm text-brand transition hover:bg-brand/10">Show more</button>}
        </ChartCard>
      </section>
    </div>
  )
}
