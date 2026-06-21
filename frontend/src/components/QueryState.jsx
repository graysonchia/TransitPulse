export function LoadingState({ className = 'h-32' }) {
  return <div className={`animate-pulse rounded-xl bg-slate-800 ${className}`} />
}

export function ErrorState({ error }) {
  return (
    <div className="rounded-xl border border-red-500/50 bg-red-950/20 p-4 text-sm text-red-300">
      {error?.response?.data?.detail || error?.message || 'Unable to load data.'}
    </div>
  )
}
