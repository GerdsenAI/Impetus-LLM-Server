import React, { useState, useEffect, useRef } from 'react'
import { Upload, FileText, Database, Trash2, RefreshCw } from 'lucide-react'
interface Collection {
  name: string
  count: number
  metadata: Record<string, unknown>
}

const styles = `
.doc-upload-container {
  padding: 1rem;
}

.doc-upload-container h3 {
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
}

.doc-upload-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.doc-upload-textarea {
  width: 100%;
  min-height: 120px;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--background-tertiary);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 0.875rem;
  resize: vertical;
  box-sizing: border-box;
}

.doc-upload-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.doc-upload-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.doc-upload-input {
  flex: 1;
  min-width: 150px;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--background-tertiary);
  color: var(--text-primary);
  font-size: 0.875rem;
}

.doc-upload-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.doc-upload-file-label {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  background: var(--background-tertiary);
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.doc-upload-file-label:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.doc-upload-file-input {
  display: none;
}

.doc-upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  background: var(--primary-color);
  color: #fff;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.doc-upload-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}

.doc-upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.doc-upload-status {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8125rem;
}

.doc-upload-status.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success-color);
}

.doc-upload-status.error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}

.doc-collections {
  margin-top: 1rem;
}

.doc-collections h4 {
  margin: 0 0 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--text-primary);
  font-size: 0.9375rem;
}

.doc-collection-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.doc-collection-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: var(--background-tertiary);
  border-radius: 6px;
  font-size: 0.8125rem;
}

.doc-collection-name {
  color: var(--text-primary);
  font-weight: 500;
}

.doc-collection-count {
  color: var(--text-secondary);
  margin-left: 0.5rem;
}

.doc-collection-delete {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
}

.doc-collection-delete:hover {
  color: var(--danger-color);
  background: rgba(239, 68, 68, 0.1);
}

.doc-empty {
  color: var(--text-secondary);
  font-size: 0.8125rem;
  font-style: italic;
}
`

if (typeof document !== 'undefined') {
  const styleEl = document.createElement('style')
  styleEl.textContent = styles
  document.head.appendChild(styleEl)
}

export function DocumentUpload(): JSX.Element {
  const [text, setText] = useState('')
  const [source, setSource] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [collections, setCollections] = useState<Collection[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchCollections = async () => {
    try {
      const res = await fetch('/api/documents/collections')
      if (res.ok) {
        const data = await res.json()
        setCollections(data.collections || [])
      }
    } catch {
      // silently fail
    }
  }

  useEffect(() => {
    fetchCollections()
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (ev) => {
      const content = ev.target?.result as string
      setText(content)
      if (!source) setSource(file.name)
    }
    reader.readAsText(file)
  }

  const handleSubmit = async () => {
    if (!text.trim()) return

    setLoading(true)
    setStatus(null)

    try {
      const res = await fetch('/api/documents/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          source: source || 'pasted-text',
        }),
      })

      const data = await res.json()

      if (res.ok) {
        setStatus({
          type: 'success',
          message: `Stored ${data.chunks_stored} chunks from "${data.source}" in "${data.collection}"`,
        })
        setText('')
        setSource('')
        if (fileInputRef.current) fileInputRef.current.value = ''
        fetchCollections()
      } else {
        setStatus({
          type: 'error',
          message: data.error?.message || 'Ingestion failed',
        })
      }
    } catch (err) {
      setStatus({
        type: 'error',
        message: `Network error: ${err instanceof Error ? err.message : String(err)}`,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCollection = async (name: string) => {
    try {
      const res = await fetch(`/api/documents/collections/${name}`, { method: 'DELETE' })
      if (res.ok) {
        fetchCollections()
      }
    } catch {
      // silently fail
    }
  }

  return (
    <div className="doc-upload-container">
      <h3>
        <Upload size={20} />
        Document Upload
      </h3>

      <div className="doc-upload-form">
        <textarea
          className="doc-upload-textarea"
          placeholder="Paste text here or upload a file (.txt, .md, .json)..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <div className="doc-upload-row">
          <input
            className="doc-upload-input"
            type="text"
            placeholder="Source name (e.g. readme.md)"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          />

          <label className="doc-upload-file-label">
            <FileText size={16} />
            Choose File
            <input
              ref={fileInputRef}
              className="doc-upload-file-input"
              type="file"
              accept=".txt,.md,.json"
              onChange={handleFileChange}
            />
          </label>

          <button
            className="doc-upload-btn"
            onClick={handleSubmit}
            disabled={loading || !text.trim()}
          >
            <Upload size={16} />
            {loading ? 'Uploading...' : 'Ingest'}
          </button>
        </div>

        {status && (
          <div className={`doc-upload-status ${status.type}`}>
            {status.message}
          </div>
        )}
      </div>

      <div className="doc-collections">
        <h4>
          <Database size={18} />
          Collections
          <button
            className="doc-collection-delete"
            onClick={fetchCollections}
            title="Refresh"
            style={{ marginLeft: 'auto' }}
          >
            <RefreshCw size={14} />
          </button>
        </h4>

        {collections.length === 0 ? (
          <p className="doc-empty">No collections yet. Ingest a document to get started.</p>
        ) : (
          <div className="doc-collection-list">
            {collections.map((col) => (
              <div key={col.name} className="doc-collection-item">
                <div>
                  <span className="doc-collection-name">{col.name}</span>
                  <span className="doc-collection-count">{col.count} docs</span>
                </div>
                <button
                  className="doc-collection-delete"
                  onClick={() => handleDeleteCollection(col.name)}
                  title={`Delete ${col.name}`}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
