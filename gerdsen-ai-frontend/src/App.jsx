import { useState } from 'react'
import './App.css'
import ModelGrid from './components/ModelGrid'
import DragDropZone from './components/DragDropZone'
import ModelSearch from './components/ModelSearch'
import { useModelWebSocket } from './hooks/useWebSocket'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Alert, AlertDescription, AlertTitle } from './components/ui/alert'
import { CheckCircle, InfoIcon, Loader, Wifi, WifiOff } from 'lucide-react'

function App() {
  const [activeTab, setActiveTab] = useState('library')
  const [notification, setNotification] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // WebSocket connection for real-time server status
  const { isConnected, serverStatus } = useModelWebSocket('http://localhost:8080')

  // Show notification helper
  const showNotification = (type, title, message) => {
    setNotification({ type, title, message })
    setTimeout(() => setNotification(null), 5000)
  }

  // Handlers for model management actions
  const handleModelLoad = (modelId, result) => {
    showNotification('success', 'Model Loaded', `Successfully loaded model: ${modelId}`)
  }

  const handleModelUnload = (modelId) => {
    showNotification('info', 'Model Unloaded', `Model ${modelId} has been unloaded`)
  }

  const handleModelSwitch = (modelId) => {
    showNotification('success', 'Model Switched', `Now using model: ${modelId}`)
  }

  const handleModelDelete = (modelId) => {
    showNotification('info', 'Model Deleted', `Model ${modelId} has been removed`)
  }

  const handleAddModel = () => {
    // Switch to upload tab when Add Model is clicked
    setActiveTab('upload')
  }

  const handleFileUpload = (file) => {
    showNotification('info', 'Upload Started', `Uploading ${file.name}...`)
  }

  const handleUploadComplete = (file, response) => {
    showNotification('success', 'Upload Complete', `${file.name} uploaded successfully`)
    // Refresh model grid after successful upload
    setRefreshKey(prev => prev + 1)
    // Switch back to library tab
    setTimeout(() => setActiveTab('library'), 1000)
  }

  const handleUploadError = (file, error) => {
    showNotification('error', 'Upload Failed', `Failed to upload ${file.name}: ${error.message}`)
  }

  const handleDownloadComplete = (modelId, data) => {
    showNotification('success', 'Download Complete', `Model ${modelId} downloaded successfully`)
    // Refresh model grid after successful download
    setRefreshKey(prev => prev + 1)
    // Switch back to library tab
    setTimeout(() => setActiveTab('library'), 1000)
  }

  const handleDownloadError = (modelId, error) => {
    showNotification('error', 'Download Failed', `Failed to download ${modelId}: ${error.message}`)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">IMPETUS Model Management</h1>
              <p className="text-sm text-gray-600">
                Intelligent Model Platform Enabling Taskbar Unified Server
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <>
                  <Wifi className="h-4 w-4 text-green-500" />
                  <span className="text-sm text-gray-600">Server Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-4 w-4 text-red-500" />
                  <span className="text-sm text-gray-600">Server Disconnected</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <Alert className={`
            ${notification.type === 'success' ? 'border-green-200 bg-green-50' : ''}
            ${notification.type === 'error' ? 'border-red-200 bg-red-50' : ''}
            ${notification.type === 'info' ? 'border-blue-200 bg-blue-50' : ''}
          `}>
            {notification.type === 'success' && <CheckCircle className="h-4 w-4" />}
            {notification.type === 'info' && <InfoIcon className="h-4 w-4" />}
            <AlertTitle>{notification.title}</AlertTitle>
            <AlertDescription>{notification.message}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-4 max-w-xl">
            <TabsTrigger value="library">Model Library</TabsTrigger>
            <TabsTrigger value="upload">Upload Model</TabsTrigger>
            <TabsTrigger value="huggingface">HuggingFace</TabsTrigger>
            <TabsTrigger value="info">About</TabsTrigger>
          </TabsList>

          {/* Model Library Tab */}
          <TabsContent value="library" className="space-y-4">
            <ModelGrid
              key={refreshKey}
              serverUrl="http://localhost:8080"
              onModelLoad={handleModelLoad}
              onModelUnload={handleModelUnload}
              onModelSwitch={handleModelSwitch}
              onModelDelete={handleModelDelete}
              onAddModel={handleAddModel}
            />
          </TabsContent>

          {/* Upload Model Tab */}
          <TabsContent value="upload" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Upload New Model</CardTitle>
                <CardDescription>
                  Add models to your library by uploading files from your computer
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DragDropZone
                  serverUrl="http://localhost:8080"
                  onFileUpload={handleFileUpload}
                  onUploadComplete={handleUploadComplete}
                  onUploadError={handleUploadError}
                />
              </CardContent>
            </Card>
          </TabsContent>

          {/* HuggingFace Tab */}
          <TabsContent value="huggingface" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Download from HuggingFace</CardTitle>
                <CardDescription>
                  Search and download models directly from the HuggingFace model hub
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ModelSearch
                  serverUrl="http://localhost:8080"
                  onDownloadComplete={handleDownloadComplete}
                  onDownloadError={handleDownloadError}
                />
              </CardContent>
            </Card>
          </TabsContent>

          {/* Info Tab */}
          <TabsContent value="info" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>About IMPETUS</CardTitle>
                <CardDescription>
                  Local LLM inference server for Apple Silicon Macs
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Features</h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                    <li>Support for 6 model formats: GGUF, SafeTensors, MLX, CoreML, PyTorch, ONNX</li>
                    <li>Real-time inference with Metal GPU acceleration</li>
                    <li>OpenAI-compatible API for VS Code integration</li>
                    <li>Dynamic hardware optimization for all Apple Silicon variants</li>
                    <li>Zero cloud dependencies - complete privacy</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Performance</h3>
                  <p className="text-sm text-gray-600">
                    Achieving 138+ tokens/sec with llama-cpp-python on Apple Silicon M3 Ultra
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">VS Code Integration</h3>
                  <p className="text-sm text-gray-600">
                    Configure Cline or Continue with base URL: <code className="bg-gray-100 px-1 py-0.5 rounded">http://localhost:8080</code>
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App
