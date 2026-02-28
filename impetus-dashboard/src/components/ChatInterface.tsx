import React, { useState, useRef, useEffect } from 'react'
import { Send, MessageSquare, BookOpen, ChevronDown } from 'lucide-react'
import { Socket } from 'socket.io-client'

interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  ragSources?: RagSource[]
}

interface RagSource {
  text: string
  source: string
  relevance: number
  chunk_index: number
}

interface ChatInterfaceProps {
  loadedModels: string[]
  socket: Socket | null
}

const styles = `
.chat-container {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.chat-container h3 {
  margin: 0 0 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
}

.chat-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.chat-model-select {
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--background-tertiary);
  color: var(--text-primary);
  font-size: 0.8125rem;
  min-width: 200px;
}

.chat-model-select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.chat-rag-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--background-tertiary);
  color: var(--text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.chat-rag-toggle.active {
  border-color: var(--primary-color);
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.5rem 0;
  max-height: 400px;
  min-height: 200px;
}

.chat-message {
  max-width: 80%;
  padding: 0.625rem 0.875rem;
  border-radius: 12px;
  font-size: 0.875rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-message.user {
  align-self: flex-end;
  background: var(--primary-color);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-message.assistant {
  align-self: flex-start;
  background: var(--background-tertiary);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

.chat-rag-sources {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-color);
}

.chat-rag-sources-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
  cursor: pointer;
}

.chat-rag-source {
  font-size: 0.75rem;
  color: var(--text-secondary);
  padding: 0.25rem 0;
}

.chat-rag-source-name {
  color: var(--primary-color);
  font-weight: 500;
}

.chat-rag-relevance {
  opacity: 0.7;
  margin-left: 0.375rem;
}

.chat-input-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.chat-input {
  flex: 1;
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--background-tertiary);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-family: inherit;
}

.chat-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.chat-send-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  background: var(--primary-color);
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.chat-send-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}

.chat-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-empty {
  color: var(--text-secondary);
  font-size: 0.8125rem;
  text-align: center;
  padding: 2rem;
  font-style: italic;
}
`

if (typeof document !== 'undefined') {
  const styleEl = document.createElement('style')
  styleEl.textContent = styles
  document.head.appendChild(styleEl)
}

export function ChatInterface({ loadedModels }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [useRag, setUseRag] = useState(false)
  const [loading, setLoading] = useState(false)
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set())
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (loadedModels.length > 0 && !selectedModel) {
      setSelectedModel(loadedModels[0])
    }
  }, [loadedModels, selectedModel])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const toggleSourceExpand = (idx: number) => {
    setExpandedSources((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || !selectedModel || loading) return

    const userMessage: ChatMessage = { role: 'user', content: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Build API messages (only user/assistant, no internal system)
    const apiMessages = [...messages, userMessage]
      .filter((m) => m.role !== 'system')
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      const res = await fetch('/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('impetus_api_key') || ''}`,
        },
        body: JSON.stringify({
          model: selectedModel,
          messages: apiMessages,
          stream: false,
          use_rag: useRag,
          rag_n_results: 5,
        }),
      })

      const data = await res.json()

      if (res.ok && data.choices?.[0]?.message) {
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: data.choices[0].message.content,
          ragSources: data.rag_sources || undefined,
        }
        setMessages((prev) => [...prev, assistantMsg])
      } else {
        const errorMsg: ChatMessage = {
          role: 'assistant',
          content: `Error: ${data.error?.message || data.error || 'Unknown error'}`,
        }
        setMessages((prev) => [...prev, errorMsg])
      }
    } catch (err) {
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: `Network error: ${err instanceof Error ? err.message : String(err)}`,
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-container">
      <h3>
        <MessageSquare size={20} />
        Chat
      </h3>

      <div className="chat-toolbar">
        <select
          className="chat-model-select"
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
        >
          {loadedModels.length === 0 && <option value="">No models loaded</option>}
          {loadedModels.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        <button
          className={`chat-rag-toggle ${useRag ? 'active' : ''}`}
          onClick={() => setUseRag(!useRag)}
        >
          <BookOpen size={14} />
          RAG {useRag ? 'ON' : 'OFF'}
        </button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            Send a message to start chatting.
            {useRag && ' RAG mode is enabled — context from your documents will be used.'}
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx}>
            <div className={`chat-message ${msg.role}`}>{msg.content}</div>

            {msg.ragSources && msg.ragSources.length > 0 && (
              <div className="chat-rag-sources" style={{ maxWidth: '80%' }}>
                <div
                  className="chat-rag-sources-header"
                  onClick={() => toggleSourceExpand(idx)}
                >
                  <BookOpen size={12} />
                  {msg.ragSources.length} source{msg.ragSources.length !== 1 ? 's' : ''}
                  <ChevronDown
                    size={12}
                    style={{
                      transform: expandedSources.has(idx) ? 'rotate(180deg)' : 'none',
                      transition: 'transform 0.2s',
                    }}
                  />
                </div>

                {expandedSources.has(idx) &&
                  msg.ragSources.map((src, si) => (
                    <div key={si} className="chat-rag-source">
                      <span className="chat-rag-source-name">[{si + 1}] {src.source}</span>
                      <span className="chat-rag-relevance">
                        ({Math.round(src.relevance * 100)}% relevant)
                      </span>
                    </div>
                  ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-message assistant" style={{ opacity: 0.6 }}>
            Thinking...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-row">
        <input
          className="chat-input"
          type="text"
          placeholder={
            selectedModel ? 'Type a message...' : 'Load a model first to chat'
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!selectedModel || loading}
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!input.trim() || !selectedModel || loading}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  )
}
