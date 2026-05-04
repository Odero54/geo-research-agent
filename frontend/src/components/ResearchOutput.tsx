import { Copy, Download, RotateCcw, FileText } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ResearchState } from '../App'

interface Props {
  state: ResearchState
  onReset: () => void
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {})
}

function downloadMarkdown(text: string) {
  const blob = new Blob([text], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `geo-research-${Date.now()}.md`
  a.click()
  URL.revokeObjectURL(url)
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-8">
      <div className="w-16 h-16 rounded-full bg-surface border border-border flex items-center justify-center text-3xl">
        🌍
      </div>
      <div>
        <p className="text-slate-300 font-medium">Ready to research</p>
        <p className="text-slate-500 text-sm mt-1 max-w-sm">
          Enter a geospatial research question on the left and choose a workflow to generate a deep research report.
        </p>
      </div>
      <div className="flex flex-wrap gap-2 justify-center mt-2">
        {[
          'Drought monitoring in sub-Saharan Africa',
          'Sentinel-1 SAR flood mapping',
          'EO foundation models comparison',
        ].map(example => (
          <span
            key={example}
            className="px-2.5 py-1 rounded-full bg-surface border border-border text-slate-500 text-xs"
          >
            {example}
          </span>
        ))}
      </div>
    </div>
  )
}

function LoadingState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-2 border-cyan-500/20" />
        <div className="absolute inset-0 rounded-full border-t-2 border-cyan-400 animate-spin" />
      </div>
      <div className="text-center">
        <p className="text-slate-300 text-sm font-medium">{message || 'Researching…'}</p>
        <p className="text-slate-600 text-xs mt-1">This may take several minutes</p>
      </div>
    </div>
  )
}

function ErrorState({ message, onReset }: { message: string; onReset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 px-8 text-center">
      <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-xl">
        ⛔
      </div>
      <div>
        <p className="text-red-400 font-medium text-sm">Research failed</p>
        <p className="text-slate-500 text-xs mt-2 max-w-sm font-mono bg-surface border border-border rounded p-3">
          {message}
        </p>
      </div>
      <button
        onClick={onReset}
        className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border
                   text-slate-400 hover:text-slate-200 hover:border-slate-500 text-sm transition-colors"
      >
        <RotateCcw className="w-4 h-4" />
        Try again
      </button>
    </div>
  )
}

export default function ResearchOutput({ state, onReset }: Props) {
  const { status, statusMessage, output, error } = state
  const hasOutput = output.length > 0
  const isStreaming = status === 'streaming'

  if (status === 'idle') return <EmptyState />
  if (status === 'loading' && !hasOutput) return <LoadingState message={statusMessage} />
  if (status === 'error') return <ErrorState message={error ?? 'Unknown error'} onReset={onReset} />

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="shrink-0 flex items-center gap-2 px-5 py-2.5 border-b border-border bg-surface">
        <FileText className="w-4 h-4 text-slate-500" />
        <span className="text-xs text-slate-500 flex-1">
          {isStreaming
            ? `Streaming… ${output.length.toLocaleString()} chars`
            : `${output.length.toLocaleString()} chars · ${Math.ceil(output.split(/\s+/).length / 200)} min read`}
        </span>

        <button
          onClick={() => copyToClipboard(output)}
          disabled={!hasOutput}
          title="Copy to clipboard"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-border
                     text-slate-400 hover:text-slate-200 hover:border-slate-500
                     text-xs transition-colors disabled:opacity-30"
        >
          <Copy className="w-3.5 h-3.5" />
          Copy
        </button>

        <button
          onClick={() => downloadMarkdown(output)}
          disabled={!hasOutput}
          title="Download as Markdown"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-border
                     text-slate-400 hover:text-slate-200 hover:border-slate-500
                     text-xs transition-colors disabled:opacity-30"
        >
          <Download className="w-3.5 h-3.5" />
          .md
        </button>

        {status === 'done' && (
          <button
            onClick={onReset}
            title="New research"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-border
                       text-slate-400 hover:text-slate-200 hover:border-slate-500
                       text-xs transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            New
          </button>
        )}
      </div>

      {/* Markdown output */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className={`prose-geo ${isStreaming ? 'cursor-blink' : ''}`}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {output}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
