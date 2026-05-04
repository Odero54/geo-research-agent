import { useState } from 'react'
import { Square, Telescope } from 'lucide-react'

interface WorkflowOption {
  id: string
  label: string
  icon: string
  description: string
}

const WORKFLOWS: WorkflowOption[] = [
  {
    id: 'orchestrated',
    label: 'Orchestrated',
    icon: '🧠',
    description: 'Full orchestrator-worker with guardrails',
  },
  {
    id: 'sequential',
    label: 'Sequential',
    icon: '➡️',
    description: 'Literature → Data → Analysis → Report',
  },
  {
    id: 'parallel',
    label: 'Parallel',
    icon: '⚡',
    description: '3 specialists simultaneously, then merged',
  },
  {
    id: 'evaluator',
    label: 'Evaluator',
    icon: '🔄',
    description: 'Generate → evaluate → refine loop',
  },
]

const DOMAINS = [
  { value: 'remote_sensing',       label: 'Remote Sensing (general)' },
  { value: 'agriculture',          label: 'Agriculture & Crop Mapping' },
  { value: 'drought_monitoring',   label: 'Drought Monitoring' },
  { value: 'flood_detection',      label: 'Flood Detection' },
  { value: 'climate',              label: 'Climate & Weather' },
  { value: 'early_warning_systems',label: 'Early Warning Systems' },
  { value: 'vegetation_health',    label: 'Vegetation Health' },
  { value: 'soil_moisture',        label: 'Soil Moisture' },
  { value: 'land_use_change',      label: 'Land Use Change' },
  { value: 'wildfire',             label: 'Wildfire' },
  { value: 'foundation_models_eo', label: 'EO Foundation Models' },
]

const DEPTHS = [
  { value: 'quick',    label: 'Quick',    hint: '~2 min' },
  { value: 'standard', label: 'Standard', hint: '~8 min' },
  { value: 'deep',     label: 'Deep',     hint: '~20 min' },
]

interface Props {
  onSubmit: (query: string, workflow: string, domain: string, depth: string) => void
  onStop: () => void
  isRunning: boolean
}

export default function QueryForm({ onSubmit, onStop, isRunning }: Props) {
  const [query, setQuery]       = useState('')
  const [workflow, setWorkflow] = useState('orchestrated')
  const [domain, setDomain]     = useState('remote_sensing')
  const [depth, setDepth]       = useState('standard')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isRunning) return
    onSubmit(query.trim(), workflow, domain, depth)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col h-full p-4 gap-5 overflow-y-auto">
      {/* Query */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-slate-400 uppercase tracking-widest">
          Research Question
        </label>
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g. Best methods for near-real-time drought monitoring in sub-Saharan Africa using EO foundation models…"
          rows={5}
          disabled={isRunning}
          className="w-full bg-surface border border-border rounded-lg p-3 text-sm text-slate-200
                     placeholder:text-slate-600 resize-none focus:outline-none focus:border-cyan-500/60
                     transition-colors disabled:opacity-50"
        />
      </div>

      {/* Workflow */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-slate-400 uppercase tracking-widest">
          Workflow
        </label>
        <div className="grid grid-cols-2 gap-2">
          {WORKFLOWS.map(wf => (
            <button
              key={wf.id}
              type="button"
              disabled={isRunning}
              onClick={() => setWorkflow(wf.id)}
              className={`flex flex-col gap-0.5 p-3 rounded-lg border text-left transition-all
                ${workflow === wf.id
                  ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-300'
                  : 'border-border bg-surface text-slate-400 hover:border-slate-600 hover:text-slate-300'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <span className="text-base leading-none">{wf.icon}</span>
              <span className="text-xs font-medium mt-1">{wf.label}</span>
              <span className="text-[10px] text-slate-500 leading-tight">{wf.description}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Domain */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-slate-400 uppercase tracking-widest">
          Domain
        </label>
        <select
          value={domain}
          onChange={e => setDomain(e.target.value)}
          disabled={isRunning}
          className="w-full bg-surface border border-border rounded-lg px-3 py-2.5 text-sm
                     text-slate-200 focus:outline-none focus:border-cyan-500/60
                     transition-colors disabled:opacity-50"
        >
          {DOMAINS.map(d => (
            <option key={d.value} value={d.value}>{d.label}</option>
          ))}
        </select>
      </div>

      {/* Depth */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-medium text-slate-400 uppercase tracking-widest">
          Research Depth
        </label>
        <div className="flex gap-2">
          {DEPTHS.map(d => (
            <button
              key={d.value}
              type="button"
              disabled={isRunning}
              onClick={() => setDepth(d.value)}
              className={`flex-1 flex flex-col items-center py-2 px-1 rounded-lg border text-xs
                transition-all disabled:opacity-50 disabled:cursor-not-allowed
                ${depth === d.value
                  ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-300'
                  : 'border-border bg-surface text-slate-400 hover:border-slate-600'
                }`}
            >
              <span className="font-medium">{d.label}</span>
              <span className="text-[10px] text-slate-500">{d.hint}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Submit / Stop */}
      <div className="mt-auto pt-2">
        {isRunning ? (
          <button
            type="button"
            onClick={onStop}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-lg
                       bg-red-500/10 border border-red-500/30 text-red-400
                       hover:bg-red-500/20 transition-colors text-sm font-medium"
          >
            <Square className="w-4 h-4" />
            Stop Research
          </button>
        ) : (
          <button
            type="submit"
            disabled={!query.trim()}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-lg
                       bg-cyan-500 text-slate-900 font-semibold text-sm
                       hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors"
          >
            <Telescope className="w-4 h-4" />
            Run Research
          </button>
        )}
      </div>
    </form>
  )
}
