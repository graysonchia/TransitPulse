import axios from 'axios'

const BASE = '/api'

export const api = {
  summary: () => axios.get(`${BASE}/ridership/summary`).then((r) => r.data),
  daily: (year, routeType) =>
    axios.get(`${BASE}/ridership/daily`, {
      params: { year, route_type: routeType || undefined },
    }).then((r) => r.data),
  byRoute: (year) =>
    axios.get(`${BASE}/ridership/by-route`, { params: { year } }).then((r) => r.data),
  heatmap: (routeType) =>
    axios.get(`${BASE}/ridership/heatmap`, {
      params: { route_type: routeType || undefined },
    }).then((r) => r.data),
  worstRoutes: () => axios.get(`${BASE}/delay/worst-routes`).then((r) => r.data),
  worstStops: () => axios.get(`${BASE}/delay/worst-stops`).then((r) => r.data),
  delayByHour: () => axios.get(`${BASE}/delay/by-hour`).then((r) => r.data),
  forecast: (days) =>
    axios.get(`${BASE}/forecast/ridership`, { params: { days_ahead: days } }).then((r) => r.data),
  anomalies: () => axios.get(`${BASE}/ml/anomalies`).then((r) => r.data),
  stopClusters: () => axios.get(`${BASE}/ml/stop-clusters`).then((r) => r.data),
  clusterProfiles: () => axios.get(`${BASE}/ml/cluster-profiles`).then((r) => r.data),
}
