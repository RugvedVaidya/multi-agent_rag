import React, { useState, useRef, useEffect } from 'react'
import { Upload, Trash2, X } from 'lucide-react'

const FILE_ICONS = { pdf:'📄', txt:'📝', md:'📋', py:'🐍', js:'🟨', ts:'🔷', cpp:'⚙️', java:'☕', go:'🐹', c:'⚙️', rs:'🦀' }
const getIcon = f => FILE_ICONS[f.split('.').pop()?.toLowerCase()] ?? '📁'

export default function Sidebar({ stats, onIngest, onReset, isIngesting }) {
  const [dragOver, setDragOver] = useState(false)
  const [queued, setQueued]     = useState([])
  const inputRef = useRef()

  const addFiles = files => {
    const arr = Array.from(files)
    setQueued(prev => {
      const names = new Set(prev.map(f => f.name))
      return [...prev, ...arr.filter(f => !names.has(f.name))]
    })
  }

  const handleDrop = e => {
    e.preventDefault(); setDragOver(false)
    addFiles(e.dataTransfer.files)
  }

  const handleIngest = async () => {
    if (!queued.length) return
    await onIngest(queued)
    setQueued([])
  }

  return (
    <aside style={{
      width: 260, flexShrink: 0,
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      height: '100vh', overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34,
            background: 'linear-gradient(135deg, #3B82F6, #6366F1)',
            borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 700, color: '#fff',
          }}>⬡</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#F1F5F9', letterSpacing: '-0.3px' }}>RAG Assistant</div>
            <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 1 }}>Groq · ChromaDB · React</div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          {[
            { val: stats.chunk_count ?? 0, lbl: 'Chunks' },
            { val: stats.files?.length ?? 0, lbl: 'Files' },
          ].map(s => (
            <div key={s.lbl} style={{
              flex: 1, background: 'var(--bg)', border: '1px solid var(--border)',
              borderRadius: 8, padding: '8px 10px', textAlign: 'center',
            }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--blue)', lineHeight: 1 }}>{s.val}</div>
              <div style={{ fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: 2 }}>{s.lbl}</div>
            </div>
          ))}
        </div>

        {/* Indexed files list */}
        {stats.files?.length > 0 && (
          <div style={{ maxHeight: 100, overflowY: 'auto' }}>
            {stats.files.map(f => (
              <div key={f} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '3px 0', fontSize: 11, color: 'var(--text3)',
              }}>
                <span>{getIcon(f)}</span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload zone */}
      <div style={{ padding: '14px 16px', flex: 1, overflow: 'auto' }}>
        <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text3)', marginBottom: 10 }}>
          Knowledge Base
        </div>

        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          style={{
            border: `1.5px dashed ${dragOver ? 'var(--blue)' : 'var(--border2)'}`,
            borderRadius: 10, padding: '18px 12px', textAlign: 'center',
            background: dragOver ? '#0F1F3A' : 'var(--bg)',
            cursor: 'pointer', transition: 'all 0.15s',
            marginBottom: 10,
          }}
        >
          <Upload size={18} color="var(--text3)" style={{ marginBottom: 6 }} />
          <div style={{ fontSize: 12, color: 'var(--text2)', fontWeight: 500 }}>Drop files or click</div>
          <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 3 }}>PDF · TXT · MD · PY · JS · more</div>
        </div>

        <input ref={inputRef} type="file" multiple hidden
          accept=".pdf,.txt,.md,.py,.js,.ts,.java,.cpp,.c,.go,.rs"
          onChange={e => addFiles(e.target.files)} />

        {/* Queued files */}
        {queued.length > 0 && (
          <div style={{ marginBottom: 10 }}>
            {queued.map((f, i) => (
              <div key={f.name} style={{
                display: 'flex', alignItems: 'center', gap: 7,
                background: 'var(--bg)', border: '1px solid var(--border)',
                borderRadius: 6, padding: '5px 8px', marginBottom: 4,
              }}>
                <span style={{ fontSize: 13 }}>{getIcon(f.name)}</span>
                <span style={{ flex: 1, fontSize: 11, color: 'var(--text2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                <button onClick={e => { e.stopPropagation(); setQueued(q => q.filter((_, j) => j !== i)) }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text3)', padding: 0, lineHeight: 1 }}>
                  <X size={12} />
                </button>
              </div>
            ))}

            <button onClick={handleIngest} disabled={isIngesting} style={{
              width: '100%', background: 'var(--blue-dark)', color: '#fff',
              border: 'none', borderRadius: 8, padding: '8px 0',
              fontSize: 12, fontWeight: 600, cursor: 'pointer',
              opacity: isIngesting ? 0.6 : 1, transition: 'all 0.15s',
              fontFamily: 'var(--sans)',
            }}>
              {isIngesting ? '⟳ Ingesting…' : `⬆ Ingest ${queued.length} file${queued.length > 1 ? 's' : ''}`}
            </button>
          </div>
        )}

        {/* Agent legend */}
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text3)', marginBottom: 8 }}>
            Agent Pipeline
          </div>
          {[
            { color: '#3B82F6', name: 'Researcher', desc: 'query rewriting + retrieval' },
            { color: '#6366F1', name: 'Analyst',    desc: 'synthesis + citations' },
            { color: '#8B5CF6', name: 'Critic',     desc: 'hallucination detection' },
          ].map(a => (
            <div key={a.name} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 8 }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: a.color, marginTop: 5, flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text2)' }}>{a.name}</div>
                <div style={{ fontSize: 10, color: 'var(--text3)' }}>{a.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Reset button */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
        <button onClick={onReset} style={{
          width: '100%', background: 'transparent',
          border: '1px solid var(--border2)', color: 'var(--text3)',
          borderRadius: 8, padding: '7px 0', fontSize: 12,
          cursor: 'pointer', display: 'flex', alignItems: 'center',
          justifyContent: 'center', gap: 6, fontFamily: 'var(--sans)',
          transition: 'all 0.15s',
        }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--red)'; e.currentTarget.style.color = 'var(--red)' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border2)'; e.currentTarget.style.color = 'var(--text3)' }}
        >
          <Trash2 size={12} /> Clear knowledge base
        </button>
      </div>
    </aside>
  )
}