import React, { useEffect, useState } from 'react'

const AGENTS = [
  { key: 'researcher', label: 'Researcher', color: '#3B82F6', desc: 'Rewrites query, retrieves chunks' },
  { key: 'analyst',    label: 'Analyst',    color: '#6366F1', desc: 'Synthesizes answer with citations' },
  { key: 'critic',     label: 'Critic',     color: '#8B5CF6', desc: 'Verifies against sources' },
]

function AgentRow({ agent, state, info }) {
  const isActive  = state === 'active'
  const isDone    = state === 'done'
  const isRevise  = state === 'revise'
  const isIdle    = state === 'idle'

  const dotColor  = isActive ? agent.color : isDone ? '#22C55E' : isRevise ? '#EF4444' : '#1E2D4A'
  const rowBg     = isActive ? '#0F1F3A' : isDone ? '#052E16' : isRevise ? '#450A0A' : 'transparent'
  const rowBorder = isActive ? `1px solid ${agent.color}33` : isDone ? '1px solid #14532D' : isRevise ? '1px solid #991B1B' : '1px solid transparent'

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '9px 12px', borderRadius: 8,
      background: rowBg, border: rowBorder,
      marginBottom: 6, transition: 'all 0.3s',
    }}>
      {/* Dot */}
      <div style={{
        width: 8, height: 8, borderRadius: '50%',
        background: dotColor, flexShrink: 0,
        boxShadow: isActive ? `0 0 8px ${agent.color}` : 'none',
        transition: 'all 0.3s',
        animation: isActive ? 'pulse 1.5s infinite' : 'none',
      }} />

      {/* Name + desc */}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, fontWeight: 500, color: isDone || isRevise ? '#E2E8F0' : '#94A3B8' }}>
          {agent.label}
        </div>
        <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 1 }}>{agent.desc}</div>
      </div>

      {/* Status */}
      <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--text3)', textAlign: 'right' }}>
        {isActive  && <span style={{ color: agent.color }}>running…</span>}
        {isDone    && <span style={{ color: '#22C55E' }}>✓ done</span>}
        {isRevise  && <span style={{ color: '#EF4444' }}>⚠ revised</span>}
        {isIdle    && <span>idle</span>}
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
    </div>
  )
}

export default function PipelineTrace({ pipelineEvents, lastResult }) {
  const [agentStates, setAgentStates] = useState({ researcher: 'idle', analyst: 'idle', critic: 'idle' })
  const [currentStage, setCurrentStage] = useState(null)

  useEffect(() => {
    if (!pipelineEvents || pipelineEvents.length === 0) {
      setAgentStates({ researcher: 'idle', analyst: 'idle', critic: 'idle' })
      setCurrentStage(null)
      return
    }

    const states = { researcher: 'idle', analyst: 'idle', critic: 'idle' }
    let stage = null

    for (const ev of pipelineEvents) {
      if (ev.type === 'status') {
        stage = ev.data.stage
        if (stage === 'researcher') states.researcher = 'active'
        if (stage === 'analyst')    { states.researcher = 'done'; states.analyst = 'active' }
        if (stage === 'critic')     { states.researcher = 'done'; states.analyst = 'done'; states.critic = 'active' }
      }
      if (ev.type === 'researcher_done') states.researcher = 'done'
      if (ev.type === 'analyst_done')    states.analyst = 'done'
      if (ev.type === 'critic_done') {
        states.critic = ev.data.verdict === 'REVISE' ? 'revise' : 'done'
      }
      if (ev.type === 'done') {
        if (states.researcher === 'active') states.researcher = 'done'
        if (states.analyst === 'active')    states.analyst = 'done'
        if (states.critic === 'active')     states.critic = 'done'
      }
    }

    setAgentStates(states)
    setCurrentStage(stage)
  }, [pipelineEvents])

  const verdict = lastResult?.critic_verdict
  const score   = lastResult?.critic_score ?? 0
  const queries = lastResult?.queries_used ?? []
  const sources = lastResult?.sources ?? []
  const pipeline= lastResult?.pipeline

  const scoreColor = score >= 0.7 ? '#22C55E' : score >= 0.4 ? '#F59E0B' : '#EF4444'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, height: '100%' }}>
      {/* Agent pipeline */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 16 }}>
        <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text3)', marginBottom: 14 }}>
          Pipeline
        </div>
        {AGENTS.map(a => (
          <AgentRow key={a.key} agent={a} state={agentStates[a.key]} />
        ))}
      </div>

      {/* Faithfulness score */}
      {lastResult && pipeline === 'rag' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text3)', marginBottom: 12 }}>
            Faithfulness
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <div style={{ flex: 1, background: 'var(--bg)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
              <div style={{ width: `${Math.round(score * 100)}%`, height: '100%', background: scoreColor, borderRadius: 4, transition: 'width 0.6s ease' }} />
            </div>
            <div style={{ fontSize: 12, fontWeight: 600, fontFamily: 'var(--mono)', color: scoreColor, minWidth: 36 }}>
              {Math.round(score * 100)}%
            </div>
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            <span style={{
              fontSize: 10, fontWeight: 700, fontFamily: 'var(--mono)',
              padding: '2px 8px', borderRadius: 20, letterSpacing: '0.5px',
              background: verdict === 'PASS' ? 'var(--green-bg)' : 'var(--red-bg)',
              color: verdict === 'PASS' ? 'var(--green)' : 'var(--red)',
            }}>{verdict}</span>
            <span style={{ fontSize: 10, color: 'var(--text3)', alignSelf: 'center' }}>
              {verdict === 'PASS' ? 'Answer verified against sources' : 'Answer was revised by critic'}
            </span>
          </div>
        </div>
      )}

      {/* Queries used */}
      {queries.length > 0 && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text3)', marginBottom: 10 }}>
            Queries Used
          </div>
          {queries.map((q, i) => (
            <div key={i} style={{
              background: 'var(--bg)', border: '1px solid var(--border)',
              borderRadius: 6, padding: '6px 10px', marginBottom: 6,
              fontSize: 11, color: 'var(--text2)', fontFamily: 'var(--mono)',
              lineHeight: 1.5,
            }}>
              {q}
            </div>
          ))}
        </div>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text3)', marginBottom: 10 }}>
            Sources Retrieved
          </div>
          {sources.map(s => {
            const ext = s.split('.').pop()?.toLowerCase()
            const icons = { pdf:'📄', txt:'📝', md:'📋', py:'🐍', js:'🟨', ts:'🔷' }
            const icon  = icons[ext] ?? '📁'
            return (
              <div key={s} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: 'var(--bg)', border: '1px solid var(--border)',
                borderRadius: 6, padding: '7px 10px', marginBottom: 6,
              }}>
                <span style={{ fontSize: 14 }}>{icon}</span>
                <span style={{ flex: 1, fontSize: 11, color: 'var(--text2)', fontFamily: 'var(--mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s}</span>
              </div>
            )
          })}
        </div>
      )}

      {!lastResult && (
        <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text3)', fontSize: 12 }}>
          Ask a question to see the pipeline run
        </div>
      )}
    </div>
  )
}