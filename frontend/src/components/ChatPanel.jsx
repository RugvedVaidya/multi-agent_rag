import React, { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send } from 'lucide-react'

const SUGGESTIONS = [
  'What are the main findings?',
  'Summarize the key points',
  'List all recommendations',
  'What does this code do?',
]

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  const verdict = msg.meta?.critic_verdict
  const score   = msg.meta?.critic_score
  const pipeline= msg.meta?.pipeline

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start', marginBottom: 20 }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', maxWidth: '85%', flexDirection: isUser ? 'row-reverse' : 'row' }}>
        {/* Avatar */}
        <div style={{
          width: 30, height: 30, borderRadius: '50%', flexShrink: 0, marginTop: 2,
          background: isUser ? '#1E2D4A' : 'linear-gradient(135deg, #3B82F6, #6366F1)',
          border: isUser ? '1px solid #2D3F5A' : 'none',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13,
        }}>
          {isUser ? '→' : '⬡'}
        </div>

        {/* Bubble */}
        <div style={{
          padding: '11px 15px',
          borderRadius: isUser ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
          background: isUser ? '#1D4ED8' : 'var(--surface)',
          border: isUser ? 'none' : '1px solid var(--border)',
          color: isUser ? '#fff' : 'var(--text)',
          fontSize: 14, lineHeight: 1.65,
        }}>
          {isUser ? (
            <span>{msg.content}</span>
          ) : (
            <div className="md-content">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>

      {/* Meta row under assistant messages */}
      {!isUser && pipeline && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 40, marginTop: 6 }}>
          {pipeline === 'rag' && verdict && (
            <>
              <span style={{
                fontSize: 10, fontWeight: 700, fontFamily: 'var(--mono)',
                padding: '2px 7px', borderRadius: 20, letterSpacing: '0.5px',
                background: verdict === 'PASS' ? 'var(--green-bg)' : 'var(--red-bg)',
                color: verdict === 'PASS' ? 'var(--green)' : 'var(--red)',
              }}>{verdict}</span>
              <span style={{ fontSize: 10, color: 'var(--text3)' }}>
                faithfulness {Math.round((score ?? 0) * 100)}%
              </span>
            </>
          )}
          {pipeline === 'chat' && (
            <span style={{ fontSize: 10, color: 'var(--text3)' }}>direct response</span>
          )}
        </div>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 20 }}>
      <div style={{
        width: 30, height: 30, borderRadius: '50%',
        background: 'linear-gradient(135deg, #3B82F6, #6366F1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13,
      }}>⬡</div>
      <div style={{
        padding: '12px 16px', borderRadius: '4px 14px 14px 14px',
        background: 'var(--surface)', border: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
          {[0, 1, 2].map(i => (
            <div key={i} style={{
              width: 6, height: 6, borderRadius: '50%', background: '#3B82F6',
              animation: `bounce 1.2s ${i * 0.2}s infinite`,
            }} />
          ))}
        </div>
        <style>{`@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-4px)} }`}</style>
      </div>
    </div>
  )
}

export default function ChatPanel({ messages, isStreaming, onSend, onSuggestion }) {
  const bottomRef  = useRef()
  const inputRef   = useRef()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      const val = inputRef.current?.value.trim()
      if (val) { onSend(val); inputRef.current.value = '' }
    }
  }

  const handleClick = () => {
    const val = inputRef.current?.value.trim()
    if (val) { onSend(val); inputRef.current.value = '' }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 24px 0' }}>
        {messages.length === 0 ? (
          /* Empty state */
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center', paddingBottom: 60 }}>
            <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>⬡</div>
            <div style={{ fontSize: 20, fontWeight: 600, color: 'var(--text3)', marginBottom: 8 }}>Ready to research</div>
            <div style={{ fontSize: 13, color: '#334155', maxWidth: 280, lineHeight: 1.7, marginBottom: 24 }}>
              Upload documents in the sidebar, then ask anything about them.
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => onSuggestion(s)} style={{
                  background: 'var(--surface)', border: '1px solid var(--border)',
                  borderRadius: 20, padding: '7px 14px', fontSize: 12,
                  color: 'var(--text2)', cursor: 'pointer', fontFamily: 'var(--sans)',
                  transition: 'all 0.15s',
                }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--blue)'; e.currentTarget.style.color = 'var(--blue)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text2)' }}
                >{s}</button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
            {isStreaming && <TypingIndicator />}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '16px 24px 24px' }}>
        <div style={{
          display: 'flex', gap: 10, alignItems: 'flex-end',
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 14, padding: '10px 12px',
          transition: 'border-color 0.15s',
        }}
          onFocusCapture={e => e.currentTarget.style.borderColor = 'var(--blue)'}
          onBlurCapture={e => e.currentTarget.style.borderColor = 'var(--border)'}
        >
          <textarea
            ref={inputRef}
            onKeyDown={handleKey}
            disabled={isStreaming}
            placeholder="Ask anything about your documents…"
            rows={1}
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: 'var(--text)', fontSize: 14, fontFamily: 'var(--sans)',
              resize: 'none', lineHeight: 1.5, maxHeight: 120, overflowY: 'auto',
            }}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
            }}
          />
          <button
            onClick={handleClick}
            disabled={isStreaming}
            style={{
              width: 34, height: 34, borderRadius: 9, flexShrink: 0,
              background: isStreaming ? 'var(--border)' : 'var(--blue-dark)',
              border: 'none', cursor: isStreaming ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.15s',
            }}
          >
            <Send size={15} color="#fff" />
          </button>
        </div>
        <div style={{ fontSize: 10, color: 'var(--text3)', textAlign: 'center', marginTop: 8 }}>
          Enter to send · Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}