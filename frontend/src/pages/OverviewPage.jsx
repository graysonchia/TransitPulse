import { useQuery } from '@tanstack/react-query'
import { Cell, Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Clock, Map, MapPin, Train, Users } from 'lucide-react'
import { api } from '../api'
import ChartCard from '../components/ChartCard'
import KPICard from '../components/KPICard'
import { ErrorState, LoadingState } from '../components/QueryState'
import { axisProps, formatNumber, gridProps, shortDate, tooltipProps } from '../components/chartTheme'

const currentYear = new Date().getFullYear()

export default function OverviewPage() {
  const summary = useQuery({ queryKey: ['summary'], queryFn: api.summary })
  const daily = useQuery({ queryKey: ['daily', currentYear, ''], queryFn: () => api.daily(currentYear, '') })
  const routes = useQuery({ queryKey: ['by-route', currentYear], queryFn: () => api.byRoute(currentYear) })
  const delays = useQuery({ queryKey: ['worst-routes'], queryFn: api.worstRoutes })
  const queries = [summary, daily, routes, delays]
  const error = queries.find((query) => query.isError)?.error

  if (error) return <ErrorState error={error} />
  if (queries.some((query) => query.isLoading)) return <LoadingState className="h-80" />

  const kpi = summary.data
  const topRoutes = routes.data.slice(0, 8)

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KPICard icon={Users} label="Total Passengers" value={formatNumber(kpi.total_passengers)} />
        <KPICard icon={Train} label="Total Trips" value={formatNumber(kpi.total_trips)} color="#a78bfa" />
        <KPICard icon={Clock} label="Avg Delay" value={`${Number(kpi.avg_delay_minutes).toFixed(2)} min`} color="#fb923c" />
        <KPICard icon={Map} label="Active Routes" value={formatNumber(kpi.active_routes)} color="#34d399" />
        <KPICard icon={MapPin} label="Active Stops" value={formatNumber(kpi.active_stops)} color="#f472b6" />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <ChartCard title="Daily Ridership Trend" className="lg:col-span-3">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={daily.data}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="full_date" tickFormatter={shortDate} {...axisProps} minTickGap={28} />
              <YAxis tickFormatter={formatNumber} {...axisProps} width={72} />
              <Tooltip {...tooltipProps} labelFormatter={(v) => new Date(`${v}T00:00:00`).toLocaleDateString()} formatter={(v) => [formatNumber(v), 'Passengers']} />
              <Line type="monotone" dataKey="total_passengers" stroke="#38bdf8" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Top Routes by Ridership" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={topRoutes} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid {...gridProps} horizontal={false} />
              <XAxis type="number" tickFormatter={formatNumber} {...axisProps} />
              <YAxis type="category" dataKey="route" width={105} {...axisProps} />
              <Tooltip {...tooltipProps} formatter={(v) => [formatNumber(v), 'Passengers']} />
              <Bar dataKey="total_passengers" radius={[0, 6, 6, 0]}>
                {topRoutes.map((route, index) => <Cell key={route.route} fill="#38bdf8" fillOpacity={1 - index * 0.08} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard title="Delay Leaders">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-400">
              <tr><th className="px-4 py-3">Route</th><th className="px-4 py-3">Avg Delay (min)</th><th className="px-4 py-3">Passengers</th></tr>
            </thead>
            <tbody>
              {delays.data.map((row, index) => (
                <tr key={row.name} className={index % 2 ? 'bg-slate-900/45' : 'bg-slate-800/20'}>
                  <td className="px-4 py-3 text-slate-200">{row.name}</td>
                  <td className={`px-4 py-3 font-semibold ${row.avg_delay_minutes > 10 ? 'text-red-400' : row.avg_delay_minutes > 5 ? 'text-orange-400' : 'text-emerald-400'}`}>{Number(row.avg_delay_minutes).toFixed(2)}</td>
                  <td className="px-4 py-3 text-slate-400">{formatNumber(row.total_passengers)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  )
}
