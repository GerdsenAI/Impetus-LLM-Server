import React, { useState, useEffect } from 'react'
import { Download, Search, Filter, Cpu, Zap, HardDrive, Check, X, Loader } from 'lucide-react'
import { Socket } from 'socket.io-client'

interface ModelBrowserProps {
  socket: Socket | null
}

interface ModelInfo {
  id: string
  name: string
  category: string
  size_gb: number
  quantization: string
  context_length: number
  description: string
  features: string[]
  recommended_for: string[]
  min_memory_gb: number
  popularity_score: number
  estimated_tokens_per_sec: number
}

interface DownloadTask {
  task_id: string
  model_id: string
  status: string
  progress: number
  downloaded_gb: number
  total_gb: number
  speed_mbps: number
  eta_seconds: number
}

const categoryIcons: Record<string, React.ReactNode> = {
  general: <Cpu size={16} />,
  coding: <>{`</>`}</>,
  chat: <>{`💬`}</>,
  efficient: <Zap size={16} />,
  specialized: <>{`🎯`}</>
}

const categoryColors: Record<string, string> = {
  general: 'category-general',
  coding: 'category-coding',
  chat: 'category-chat',
  efficient: 'category-efficient',
  specialized: 'category-specialized'
}

export const ModelBrowser: React.FC<ModelBrowserProps> = ({ socket }) => {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [filteredModels, setFilteredModels] = useState<ModelInfo[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [downloads, setDownloads] = useState<Map<string, DownloadTask>>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchModels()
  }, [])

  useEffect(() => {
    if (!socket) return

    // Subscribe to download progress
    socket.on('download_progress', (data) => {
      setDownloads(prev => {
        const updated = new Map(prev)
        updated.set(data.task_id, data)
        return updated
      })
    })

    socket.on('download_complete', (data) => {
      if (data.success) {
        // Remove from downloads after a delay
        setTimeout(() => {
          setDownloads(prev => {
            const updated = new Map(prev)
            updated.delete(data.task_id)
            return updated
          })
        }, 3000)
      }
    })

    return () => {
      socket.off('download_progress')
      socket.off('download_complete')
    }
  }, [socket])

  useEffect(() => {
    // Filter models based on category and search
    let filtered = models

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(m => m.category === selectedCategory)
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(m => 
        m.name.toLowerCase().includes(query) ||
        m.description.toLowerCase().includes(query) ||
        m.features.some(f => f.toLowerCase().includes(query))
      )
    }

    setFilteredModels(filtered)
  }, [models, selectedCategory, searchQuery])

  const fetchModels = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/models/discover')
      const data = await response.json()
      setModels(data.models || [])
      setError(null)
    } catch (err) {
      console.error('Failed to fetch models:', err)
      setError('Failed to load models')
    } finally {
      setLoading(false)
    }
  }

  const downloadModel = async (modelId: string) => {
    try {
      const response = await fetch('/api/models/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId, auto_load: true })
      })
      
      const data = await response.json()
      
      if (response.ok && socket) {
        // Subscribe to this download's progress
        socket.emit('subscribe_download', { task_id: data.task_id })
        
        // Add initial download task
        setDownloads(prev => {
          const updated = new Map(prev)
          updated.set(data.task_id, {
            task_id: data.task_id,
            model_id: modelId,
            status: 'downloading',
            progress: 0,
            downloaded_gb: 0,
            total_gb: data.estimated_size_gb,
            speed_mbps: 0,
            eta_seconds: 0
          })
          return updated
        })
      } else {
        setError(data.error || 'Failed to start download')
      }
    } catch (err) {
      console.error('Download error:', err)
      setError('Failed to start download')
    }
  }

  const getDownloadForModel = (modelId: string): DownloadTask | undefined => {
    for (const task of downloads.values()) {
      if (task.model_id === modelId) {
        return task
      }
    }
    return undefined
  }

  const formatETA = (seconds: number): string => {
    if (!seconds || seconds < 0) return '--'
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  }

  const categories = ['all', 'general', 'coding', 'chat', 'efficient', 'specialized']

  return (
    <div className="model-browser">
      <div className="browser-header">
        <h2 className="section-title">Model Browser</h2>
        <div className="browser-controls">
          <div className="search-box">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Search models..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
          
          <div className="category-filters">
            {categories.map(cat => (
              <button
                key={cat}
                className={`filter-btn ${selectedCategory === cat ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat === 'all' ? <Filter size={14} /> : categoryIcons[cat]}
                <span>{cat}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <span>Loading models...</span>
        </div>
      ) : (
        <div className="models-grid">
          {filteredModels.map(model => {
            const download = getDownloadForModel(model.id)
            const isDownloading = download?.status === 'downloading'
            const isCompleted = download?.status === 'completed'
            
            return (
              <div key={model.id} className={`model-card ${categoryColors[model.category]}`}>
                <div className="model-header">
                  <div className="model-title">
                    <h3>{model.name}</h3>
                    <span className="model-quantization">{model.quantization}</span>
                  </div>
                  <div className="model-category">
                    {categoryIcons[model.category]}
                  </div>
                </div>
                
                <p className="model-description">{model.description}</p>
                
                <div className="model-specs">
                  <div className="spec">
                    <HardDrive size={14} />
                    <span>{model.size_gb.toFixed(1)} GB</span>
                  </div>
                  <div className="spec">
                    <Zap size={14} />
                    <span>~{model.estimated_tokens_per_sec} tok/s</span>
                  </div>
                  <div className="spec">
                    <span className="context-length">{(model.context_length / 1000).toFixed(0)}k ctx</span>
                  </div>
                </div>
                
                <div className="model-features">
                  {model.features.slice(0, 3).map((feature, idx) => (
                    <span key={idx} className="feature-tag">{feature}</span>
                  ))}
                </div>
                
                <div className="model-actions">
                  {isDownloading ? (
                    <div className="download-progress">
                      <div className="progress-info">
                        <span>{(download.progress * 100).toFixed(0)}%</span>
                        <span>{download.speed_mbps.toFixed(1)} MB/s</span>
                        <span>ETA: {formatETA(download.eta_seconds)}</span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ width: `${download.progress * 100}%` }}
                        />
                      </div>
                    </div>
                  ) : isCompleted ? (
                    <button className="button-success" disabled>
                      <Check size={16} />
                      Downloaded
                    </button>
                  ) : (
                    <button 
                      className="button-primary"
                      onClick={() => downloadModel(model.id)}
                    >
                      <Download size={16} />
                      Download
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// Add styles
const styles = `
.model-browser {
  min-height: 600px;
}

.browser-header {
  margin-bottom: 2rem;
}

.browser-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1.5rem;
}

.search-box {
  position: relative;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 3rem;
  background: var(--background-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.875rem;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.category-filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--background-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  background: var(--background-secondary);
  color: var(--text-primary);
}

.filter-btn.active {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 1.5rem;
}

.model-card {
  background: var(--background-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.2s;
}

.model-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.category-general {
  border-top: 3px solid var(--primary-color);
}

.category-coding {
  border-top: 3px solid #ff9500;
}

.category-chat {
  border-top: 3px solid #34c759;
}

.category-efficient {
  border-top: 3px solid #5ac8fa;
}

.category-specialized {
  border-top: 3px solid #af52de;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.model-title {
  flex: 1;
}

.model-title h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
  color: var(--text-primary);
}

.model-quantization {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  background: var(--background-secondary);
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.model-category {
  color: var(--text-secondary);
}

.model-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 1rem;
  line-height: 1.5;
}

.model-specs {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.spec {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--text-secondary);
}

.context-length {
  padding: 0.125rem 0.5rem;
  background: var(--background-secondary);
  border-radius: 4px;
  font-size: 0.75rem;
}

.model-features {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.feature-tag {
  padding: 0.25rem 0.75rem;
  background: var(--background-secondary);
  border-radius: 100px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.model-actions {
  margin-top: 1rem;
}

.button-primary {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.button-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.button-success {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--success-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: default;
  opacity: 0.7;
}

.download-progress {
  background: var(--background-secondary);
  border-radius: 8px;
  padding: 1rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.progress-bar {
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.3s ease;
}
`

if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style')
  styleSheet.textContent = styles
  document.head.appendChild(styleSheet)
}