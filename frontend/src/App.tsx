import { useRef, useState } from 'react'
import Header from './components/Header'
import QueryForm from './components/QueryForm'
import ResearchOutput from './components/ResearchOutput'

export type Status = 'idle' | 'loading' | 'streaming' | 'done' | 'error'

export interface ResearchState {
  status: Status
  statusMessage: string
  output: string
  error?: string
}

export default function App() {
  const [state, setState] = useState<ResearchState>({
    status: 'idle',
    statusMessage: '',
    output: '',
  })
  const abortRef = useRef<AbortController | null>(null)

  const handleSubmit = async (
    query: string,
    workflow: string,
    domain: string,
    depth: string,
  ) => {
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setState({ status: 'loading', statusMessage: 'Connecting...', output: '' })

    try {
      const response = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, workflow, domain, depth }),
        signal: abortRef.current.signal,
      })

      if (!response.ok) {
        const err = await response.text()
        throw new Error(`Server error ${response.status}: ${err}`)
      }
      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'status') {
              setState(s => ({ ...s, status: 'loading', statusMessage: event.message }))
            } else if (event.type === 'chunk') {
              setState(s => ({
                ...s,
                status: 'streaming',
                output: s.output + event.content,
              }))
            } else if (event.type === 'done') {
              setState(s => ({ ...s, status: 'done', statusMessage: 'Research complete' }))
            } else if (event.type === 'error') {
              setState(s => ({ ...s, status: 'error', error: event.message }))
            }
          } catch {
            // malformed SSE line — skip
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      setState(s => ({ ...s, status: 'error', error: String(err) }))
    }
  }

  const handleStop = () => {
    abortRef.current?.abort()
    setState(s => ({ ...s, status: 'done', statusMessage: 'Stopped' }))
  }

  const handleReset = () => {
    setState({ status: 'idle', statusMessage: '', output: '' })
  }

  const isRunning = state.status === 'loading' || state.status === 'streaming'

  return (
    <div className="h-full flex flex-col bg-base">
      <Header status={state.status} statusMessage={state.statusMessage} />

      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar — query form */}
        <aside className="w-[380px] shrink-0 border-r border-border flex flex-col overflow-hidden">
          <QueryForm
            onSubmit={handleSubmit}
            onStop={handleStop}
            isRunning={isRunning}
          />
        </aside>

        {/* Right panel — output */}
        <main className="flex-1 overflow-hidden flex flex-col">
          <ResearchOutput state={state} onReset={handleReset} />
        </main>
      </div>
    </div>
  )
}
