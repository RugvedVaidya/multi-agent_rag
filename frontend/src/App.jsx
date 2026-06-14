import React, { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import PipelineTrace from './components/PipelineTrace'

export default function App() {
  const [messages,       setMessages]       = useState([])
  const [isStreaming,    setIsStreaming]     = useState(false)
  const [isIngesting,    setIsIngesting]     = useState(false)
  const [stats,          setStats]           = useState({ chunk_count: 0, files: [] })
  const [pipelineEvents, setPipelineEvents]  = useState([])
  const [lastResult,     setLastResult]      = useState(null)

  // ── Load stats on mount ──────────────────────────────────────
  const loadStats = useCallback(async () => {
    try {
      const r = await fetch('/stats')
      if (r.ok) setStats(await r.json())
    } catch {}
  }, [])

  useEffect(() => { loadStats() }, [loadStats])

  // ── Send a message ───────────────────────────────────────────
  const sendMessage = useCallback(async (question) => {
    if (!question.trim() || isStreaming) return

    const userMsg = { role: 'user', content: question }
    setMessages(prev => [...prev, userMsg])
    setIsStreaming(true)
    setPipelineEvents([])

    const history = messages.map(m => ({ role: m.role, content: m.content }))

    try {
      const res = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader  = res.body.getReader()
      const decoder = new TextDecoder()
      let   buffer  = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() ?? ''

        for (const part of parts) {
          const lines     = part.split('\n')
          const eventLine = lines.find(l => l.startsWith('event:'))
          const dataLine  = lines.find(l => l.startsWith('data:'))

          if (!eventLine || !dataLine) continue

          const eventType = eventLine.replace('event:', '').trim()
          let   data      = {}
          try { data = JSON.parse(dataLine.replace('data:', '').trim()) } catch {}

          setPipelineEvents(prev => [...prev, { type: eventType, data }])

          if (eventType === 'done') {
            setLastResult(data)
            setMessages(prev => [...prev, {
              role:    'assistant',
              content: data.answer,
              meta:    data,
            }])
          }
        }
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}. Make sure the backend is running on port 8000.`,
        meta: null,
      }])
    } finally {
      setIsStreaming(false)
    }
  }, [messages, isStreaming])

  // ── Ingest files ─────────────────────────────────────────────
  const handleIngest = useCallback(async (files) => {
    setIsIngesting(true)
    try {
      const form = new FormData()
      files.forEach(f => form.append('files', f))
      const r = await fetch('/ingest', { method: 'POST', body: form })
      if (r.ok) {
        const data = await r.json()
        await loadStats()
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✓ Ingested **${data.ingested.join(', ')}** — ${data.total_chunks} total chunks indexed.`,
          meta: { pipeline: 'chat', critic_verdict: 'PASS', critic_score: 1 },
        }])
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Failed to ingest files: ${err.message}`,
        meta: null,
      }])
    } finally {
      setIsIngesting(false)
    }
  }, [loadStats])

  // ── Reset DB ─────────────────────────────────────────────────
  const handleReset = useCallback(async () => {
    if (!confirm('Clear the entire knowledge base? This cannot be undone.')) return
    try {
      await fetch('/reset', { method: 'DELETE' })
      await loadStats()
      setMessages([])
      setLastResult(null)
      setPipelineEvents([])
    } catch {}
  }, [loadStats])

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <Sidebar
        stats={stats}
        onIngest={handleIngest}
        onReset={handleReset}
        isIngesting={isIngesting}
      />

      {/* Chat */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, borderRight: '1px solid var(--border)' }}>
        {/* Header */}
        <div style={{
          padding: '14px 24px',
          borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: '#F1F5F9' }}>Research Chat</div>
            <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 1 }}>
              {stats.chunk_count > 0
                ? `${stats.chunk_count} chunks indexed across ${stats.files?.length ?? 0} file(s)`
                : 'No documents ingested yet'}
            </div>
          </div>
          {messages.length > 0 && (
            <button onClick={() => { setMessages([]); setLastResult(null); setPipelineEvents([]) }}
              style={{
                background: 'transparent', border: '1px solid var(--border)',
                color: 'var(--text3)', borderRadius: 7, padding: '5px 12px',
                fontSize: 12, cursor: 'pointer', fontFamily: 'var(--sans)',
              }}>
              Clear chat
            </button>
          )}
        </div>

        {/* Chat panel */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            onSend={sendMessage}
            onSuggestion={sendMessage}
          />
        </div>
      </div>

      {/* Pipeline trace */}
      <div style={{ width: 320, flexShrink: 0, padding: 16, overflowY: 'auto' }}>
        <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text3)', marginBottom: 12 }}>
          Pipeline Trace
        </div>
        <PipelineTrace
          pipelineEvents={pipelineEvents}
          lastResult={lastResult}
        />
      </div>
    </div>
  )
}