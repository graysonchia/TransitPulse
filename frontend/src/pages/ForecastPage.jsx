import { useQuery } from '@tanstack/react-query'
import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import ChartCard from '../components/ChartCard'
import { ErrorState, LoadingState } from '../components/QueryState'
import { axisProps, formatNumber, gridProps, shortDate, tooltipProps } from '../components/chartTheme'

export default function ForecastPage() {
  const forecast = useQuery({ queryKey: ['forecast', 90], queryFn: () => api.forecast(90) })
  if (forecast.isLoading) return <LoadingState className="h-96" />
  if (forecast.isError) return <ErrorState error={forecast.error} />

  const data = forecast.data.map((row) => ({
    ...row,
    historical: row.is_forecast ? null : row.yhat,
    forecast: row.is_forecast ? row.yhat : null,
    band: Math.max(0, row.yhat_upper - row.yhat_lower),
  }))
  const future = forecast.data.filter((row) => row.is_forecast)

  return (
    <div className="space-y-6">
      <ChartCard title="Prophet Forecast — Next 90 Days">
        <ResponsiveContainer width="100%" height={420}>
          <ComposedChart data={data}>
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="date" tickFormatter={shortDate} {...axisProps} minTickGap={28} />
            <YAxis tickFormatter={formatNumber} {...axisProps} width={75} />
            <Tooltip {...tooltipProps} formatter={(v) => formatNumber(v)} />
            <Legend />
            <Area type="monotone" dataKey="yhat_lower" stackId="confidence" stroke="none" fill="transparent" legendType="none" />
            <Area type="monotone" dataKey="band" stackId="confidence" stroke="none" fill="#38bdf8" fillOpacity={0.15} name="Confidence Band" />
            <Line type="monotone" dataKey="historical" stroke="#38bdf8" strokeWidth={2} dot={false} name="Historical" connectNulls={false} />
            <Line type="monotone" dataKey="forecast" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Forecast" connectNulls={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="14-Day Forecast Preview">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-400"><tr><th className="px-4 py-3">Date</th><th className="px-4 py-3">Predicted Passengers</th><th className="px-4 py-3">Lower Bound</th><th className="px-4 py-3">Upper Bound</th></tr></thead>
            <tbody>
              {future.slice(0, 14).map((row, index) => (
                <tr key={row.date} className={index % 2 ? 'bg-slate-900/45' : 'bg-slate-800/20'}>
                  <td className="px-4 py-3 text-slate-200">{new Date(`${row.date}T00:00:00`).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-amber-300">{formatNumber(Math.round(row.yhat))}</td>
                  <td className="px-4 py-3 text-slate-400">{formatNumber(Math.round(row.yhat_lower))}</td>
                  <td className="px-4 py-3 text-slate-400">{formatNumber(Math.round(row.yhat_upper))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ChartCard>
    </div>
  )
}
