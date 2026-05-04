import { Globe } from 'lucide-react'
import type { Status } from '../App'

interface Props {
  status: Status
  statusMessage: string
}

const statusConfig: Record<Status, { dot: string; label: string }> = {
  idle:      { dot: 'bg-slate-600',  label: 'Ready' },
  loading:   { dot: 'bg-yellow-400 animate-pulse', label: '' },
  streaming: { dot: 'bg-cyan-400 animate-pulse',   label: '' },
  done:      { dot: 'bg-emerald-400', label: 'Complete' },
  error:     { dot: 'bg-red-400',     label: 'Error' },
}

export default function Header({ status, statusMessage }: Props) {
  const cfg = statusConfig[status]
  const label = statusMessage || cfg.label

  return (
    <header className="h-12 shrink-0 border-b border-border flex items-center px-5 gap-3 bg-surface">
      <Globe className="w-5 h-5 text-cyan-400" strokeWidth={1.5} />
      <span className="font-semibold text-slate-100 tracking-tight">GeoResearch AI</span>
      <span className="text-slate-600 text-sm hidden sm:block">
        Deep Research for Geospatial Scientists
      </span>

      {label && (
        <div className="ml-auto flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
          <span className="text-xs text-slate-400 max-w-xs truncate">{label}</span>
        </div>
      )}
    </header>
  )
}
