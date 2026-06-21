export const gridProps = { stroke: '#1e293b', strokeDasharray: '3 3' }
export const axisProps = {
  tick: { fill: '#64748b', fontSize: 12 },
  axisLine: { stroke: '#334155' },
  tickLine: false,
}
export const tooltipProps = {
  contentStyle: { background: '#0f172a', border: '1px solid #334155', borderRadius: 10 },
  labelStyle: { color: '#e5edf7' },
  itemStyle: { color: '#e5edf7' },
}

export const shortDate = (value) =>
  new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

export const formatNumber = (value) => Number(value || 0).toLocaleString()
