export default function ChartCard({ title, children, className = '' }) {
  return (
    <section className={`rounded-2xl border border-[rgba(148,163,184,0.15)] bg-[#0f172a] p-5 ${className}`}>
      <h3 className="mb-5 text-sm font-semibold uppercase tracking-wider text-slate-300">{title}</h3>
      {children}
    </section>
  )
}
