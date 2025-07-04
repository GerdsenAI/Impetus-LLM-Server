import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import { Button } from '@/components/ui/button.jsx'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState('')

  const handleQueryChange = (event) => {
    setQuery(event.target.value)
  }

  const handleSubmitQuery = () => {
    // Placeholder for AI model integration
    setResponse(`Response to: "${query}" - This is a placeholder until AI integration is complete.`)
    setQuery('')
  }

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div>
        <Button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </Button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>
      <div className="ai-query-section">
        <h2>AI Query</h2>
        <textarea 
          value={query} 
          onChange={handleQueryChange} 
          placeholder="Enter your AI query here..." 
          rows="3" 
          style={{ width: '100%', maxWidth: '500px', marginBottom: '10px' }}
        />
        <Button onClick={handleSubmitQuery} disabled={!query.trim()}>
          Submit Query
        </Button>
        {response && (
          <div className="ai-response" style={{ marginTop: '20px', padding: '10px', border: '1px solid #ccc', borderRadius: '5px', maxWidth: '500px' }}>
            <h3>AI Response:</h3>
            <p>{response}</p>
          </div>
        )}
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
