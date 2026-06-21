import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Cell, CartesianGrid, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import ChartCard from '../components/ChartCard'
import { ErrorState, LoadingState } from '../components/QueryState'
import { axisProps, formatNumber, gridProps, shortDate, tooltipProps } from '../components/chartTheme'

const currentYear = new Date().getFullYear()
const routeColors = { LRT: '#38bdf8', MRT: '#a78bfa', BUS: '#34d399', KTM: '#fb923c', Monorail: '#f472b6', Unknown: '#94a3b8' }
const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function Heatmap({ data }) {
  const lookup = new Map(data.map((cell) => [`${cell.weekday}-${cell.hour}`, cell.total_passengers]))
  const max = Math.max(...data.map((cell) => Number(cell.total_passengers)), 1)
  const color = (value) => {
    const ratio = Number(value || 0) / max
    return `rgb(${Math.round(15 + 41 * ratio)}, ${Math.round(23 + 166 * ratio)}, ${Math.round(42 + 206 * ratio)})`
  }
  return (
    <div className="overflow-x-auto pb-2">
      <div className="grid min-w-[940px] gap-1" style={{ gridTemplateColumns: '52px repeat(24, 36px)' }}>
        <div />
        {Array.from({ length: 24 }, (_, hour) => <div key={hour} className="text-center text-[10px] text-slate-500">{hour}</div>)}
        {weekdays.flatMap((day, dayIndex) => [
          <div key={`${day}-label`} className="flex items-center text-xs text-slate-400">{weekdayLabels[dayIndex]}</div>,
          ...Array.from({ length: 24 }, (_, hour) => {
            const value = lookup.get(`${day}-${hour}`) ?? lookup.get(`${weekdayLabels[dayIndex]}-${hour}`) ?? 0
            return <div key={`${day}-${hour}`} title={`${day}, ${hour}:00 — ${formatNumber(value)} passengers`} className="h-7 rounded-sm border border-slate-800/60" style={{ backgroundColor: color(value) }} />
          }),
        ])}
      </div>
    </div>
  )
}

export default function RidershipPage() {
  const [selectedYear, setSelectedYear] = useState(currentYear)
  const [selectedRouteType, setSelectedRouteType] = useState('')
  const daily = useQuery({ queryKey: ['daily', selectedYear, selectedRouteType], queryFn: () => api.daily(selectedYear, selectedRouteType) })
  const heatmap = useQuery({ queryKey: ['heatmap', selectedRouteType], queryFn: () => api.heatmap(selectedRouteType) })
  const routes = useQuery({ queryKey: ['by-route', selectedYear], queryFn: () => api.byRoute(selectedYear) })
  const queries = [daily, heatmap, routes]
  const routeTypes = useMemo(() => {
    const totals = {}
    for (const row of routes.data || []) totals[row.route_type || 'Unknown'] = (totals[row.route_type || 'Unknown'] || 0) + Number(row.total_passengers)
    return Object.entries(totals).map(([name, value]) => ({ name, value }))
  }, [routes.data])
  const years = Array.from({ length: Math.max(currentYear - 2024 + 1, 1) }, (_, i) => currentYear - i)

  const error = queries.find((query) => query.isError)?.error
  if (error) return <ErrorState error={error} />

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3">
        <select value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))} className="rounded-lg border border-slate-700 bg-[#0f172a] px-3 py-1.5 text-white">
          {years.map((year) => <option key={year}>{year}</option>)}
        </select>
        <select value={selectedRouteType} onChange={(e) => setSelectedRouteType(e.target.value)} className="rounded-lg border border-slate-700 bg-[#0f172a] px-3 py-1.5 text-white">
          {['', 'LRT', 'MRT', 'BUS', 'KTM', 'Monorail'].map((type) => <option key={type} value={type}>{type || 'All Route Types'}</option>)}
        </select>
      </div>

      {queries.some((query) => query.isLoading) ? <LoadingState className="h-80" /> : (
        <>
          <div className="grid gap-6 lg:grid-cols-2">
            <ChartCard title="Daily Ridership">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={daily.data}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="full_date" tickFormatter={shortDate} {...axisProps} minTickGap={28} />
                  <YAxis tickFormatter={formatNumber} {...axisProps} width={72} />
                  <Tooltip {...tooltipProps} formatter={(v) => [formatNumber(v), 'Passengers']} />
                  <Line type="monotone" dataKey="total_passengers" stroke="#38bdf8" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard title="Ridership by Route Type">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={routeTypes} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2}>
                    {routeTypes.map((row) => <Cell key={row.name} fill={routeColors[row.name] || routeColors.Unknown} />)}
                  </Pie>
                  <Tooltip {...tooltipProps} formatter={(v) => formatNumber(v)} />
                  <Legend verticalAlign="bottom" />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
          <ChartCard title="Hour × Weekday Ridership Heatmap"><Heatmap data={heatmap.data} /></ChartCard>
        </>
      )}
    </div>
  )
}
