import { useState } from 'react'
import reactLogo from './assets/react.svg'
import './App.css'
import ModelGrid from './components/ModelGrid'

function App() {
  // Optionally, you can add state for notifications, errors, etc.

  // Handlers for model management actions (can be expanded)
  const handleModelLoad = (modelId, result) => {
    // Optionally show notification or update state
    console.log('Model loaded:', modelId, result)
  }
  const handleModelUnload = (modelId) => {
    console.log('Model unloaded:', modelId)
  }
  const handleModelSwitch = (modelId) => {
    console.log('Switched to model:', modelId)
  }
  const handleModelDelete = (modelId) => {
    console.log('Deleted model:', modelId)
  }
  const handleAddModel = () => {
    // Open file dialog or show upload modal (to be implemented)
    alert('Add Model functionality coming soon!')
  }

  return (
    <>
      <div>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Impetus Model Management</h1>
      <div style={{ margin: '2rem 0' }}>
        <ModelGrid
          serverUrl="http://localhost:8080"
          onModelLoad={handleModelLoad}
          onModelUnload={handleModelUnload}
          onModelSwitch={handleModelSwitch}
          onModelDelete={handleModelDelete}
          onAddModel={handleAddModel}
        />
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
