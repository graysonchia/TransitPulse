import { useQuery } from '@tanstack/react-query'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import ChartCard from '../components/ChartCard'
import { ErrorState, LoadingState } from '../components/QueryState'
import { axisProps, gridProps, tooltipProps } from '../components/chartTheme'

const delayColor = (value) => value > 10 ? '#ef4444' : value > 5 ? '#f97316' : '#eab308'

function DelayBars({ data }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} layout="vertical" margin={{ left: 15 }}>
        <CartesianGrid {...gridProps} horizontal={false} />
        <XAxis type="number" {...axisProps} />
        <YAxis type="category" dataKey="name" width={115} {...axisProps} />
        <Tooltip {...tooltipProps} formatter={(v) => [`${Number(v).toFixed(2)} min`, 'Avg delay']} />
        <Bar dataKey="avg_delay_minutes" radius={[0, 6, 6, 0]}>
          {data.map((row) => <Cell key={row.name} fill={delayColor(row.avg_delay_minutes)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function DelaysPage() {
  const routes = useQuery({ queryKey: ['worst-routes'], queryFn: api.worstRoutes })
  const stops = useQuery({ queryKey: ['worst-stops'], queryFn: api.worstStops })
  const hourly = useQuery({ queryKey: ['delay-by-hour'], queryFn: api.delayByHour })
  const queries = [routes, stops, hourly]
  const error = queries.find((query) => query.isError)?.error
  if (error) return <ErrorState error={error} />
  if (queries.some((query) => query.isLoading)) return <LoadingState className="h-80" />

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Worst Routes by Avg Delay"><DelayBars data={routes.data} /></ChartCard>
        <ChartCard title="Worst Stops by Avg Delay"><DelayBars data={stops.data} /></ChartCard>
      </div>
      <ChartCard title="Average Delay by Hour of Day">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={hourly.data}>
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="hour" {...axisProps} />
            <YAxis {...axisProps} />
            <Tooltip {...tooltipProps} formatter={(v) => [`${Number(v).toFixed(2)} min`, 'Avg delay']} />
            {[7, 8, 9, 17, 18, 19].map((hour) => <ReferenceLine key={hour} x={hour} stroke="#64748b" strokeDasharray="3 3" label={{ value: 'Peak', fill: '#94a3b8', fontSize: 10 }} />)}
            <Area type="monotone" dataKey="avg_delay_minutes" stroke="#f97316" fill="#f97316" fillOpacity={0.3} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  )
}
