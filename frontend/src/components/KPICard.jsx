export default function KPICard({ icon: Icon, label, value, sub, color = '#38bdf8' }) {
  return (
    <div className="rounded-2xl border border-[rgba(148,163,184,0.18)] bg-[rgba(15,23,42,0.8)] p-5 shadow-xl shadow-black/10">
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-full" style={{ backgroundColor: `${color}1f` }}>
        <Icon size={24} color={color} />
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="mt-1 text-sm text-slate-400">{label}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  )
}
