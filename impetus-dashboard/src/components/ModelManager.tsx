import React, { useState, useEffect } from 'react'
import { Download, Trash2, Play } from 'lucide-react'
import { Socket } from 'socket.io-client'

interface ModelManagerProps {
  loadedModels: string[]
  socket: Socket | null
}

interface Model {
  id: string
  name: string
  format: string
  size_gb: number
  loaded: boolean
  path: string
}

export const ModelManager: React.FC<ModelManagerProps> = ({ loadedModels }) => {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    fetchModels()
  }, [loadedModels])

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/models/list')
      const data = await response.json()
      setModels(data.models || [])
    } catch (e) {
      console.error('Failed to fetch models:', e)
      setError('Failed to fetch models')
    }
  }

  const loadModel = async (modelId: string) => {
    setLoading(modelId)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch('/api/models/load', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_id: modelId }),
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess(`Model ${modelId} loaded successfully`)
        await fetchModels()
      } else {
        setError(data.error || 'Failed to load model')
      }
    } catch {
      setError('Network error while loading model')
    } finally {
      setLoading(null)
    }
  }

  const unloadModel = async (modelId: string) => {
    setLoading(modelId)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch('/api/models/unload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_id: modelId }),
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess(`Model ${modelId} unloaded successfully`)
        await fetchModels()
      } else {
        setError(data.error || 'Failed to unload model')
      }
    } catch {
      setError('Network error while unloading model')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="model-manager">
      <div className="model-manager-header">
        <h2 className="section-title">Model Manager</h2>
        <div className="model-actions">
          <button className="button-secondary">
            <Download size={16} />
            Download Model
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      <div className="models-grid">
        {models.length === 0 ? (
          <div className="empty-state">
            <p>No models found. Download a model to get started.</p>
          </div>
        ) : (
          models.map((model) => (
            <div key={model.id} className={`model-card ${model.loaded ? 'loaded' : ''}`}>
              <div className="model-info">
                <h3 className="model-name">{model.name}</h3>
                <div className="model-meta">
                  <span className="model-format">{model.format.toUpperCase()}</span>
                  <span className="model-size">{model.size_gb.toFixed(1)} GB</span>
                </div>
              </div>
              
              <div className="model-actions">
                {loading === model.id ? (
                  <div className="loading-spinner"></div>
                ) : model.loaded ? (
                  <button 
                    className="button-danger"
                    onClick={() => unloadModel(model.id)}
                    title="Unload model"
                  >
                    <Trash2 size={16} />
                  </button>
                ) : (
                  <button 
                    className="button-primary"
                    onClick={() => loadModel(model.id)}
                    title="Load model"
                  >
                    <Play size={16} />
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="model-info-footer">
        <p className="info-text">
          Loaded models: {loadedModels.length} / {models.filter(m => m.loaded).length}
        </p>
      </div>
    </div>
  )
}

// Add styles
const styles = `
.model-manager {
  min-height: 300px;
}

.model-manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.model-actions {
  display: flex;
  gap: 0.5rem;
}

.button-secondary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--background-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.button-secondary:hover {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.button-primary {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.button-primary:hover {
  transform: scale(1.05);
}

.button-danger {
  background: var(--danger-color);
  color: white;
  border: none;
  padding: 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.button-danger:hover {
  transform: scale(1.05);
}

.models-grid {
  display: grid;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.model-card {
  background: var(--background-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;
}

.model-card.loaded {
  border-color: var(--success-color);
  background: rgba(52, 199, 89, 0.05);
}

.model-info {
  flex: 1;
}

.model-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: var(--text-primary);
}

.model-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.model-format {
  background: var(--background-secondary);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}

.model-info-footer {
  border-top: 1px solid var(--border-color);
  padding-top: 1rem;
}

.info-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
}
`

if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style')
  styleSheet.textContent = styles
  document.head.appendChild(styleSheet)
}