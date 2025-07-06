/**
 * Test data and mock requests for IMPETUS testing
 */

const testData = {
  // Sample chat messages for testing
  chatMessages: {
    simple: [
      { role: 'user', content: 'Hello, this is a test message.' }
    ],
    conversation: [
      { role: 'user', content: 'What is machine learning?' },
      { role: 'assistant', content: 'Machine learning is a subset of artificial intelligence...' },
      { role: 'user', content: 'Can you give me an example?' }
    ],
    codeRequest: [
      { role: 'user', content: 'Write a simple Python function to calculate fibonacci numbers.' }
    ],
    longConversation: [
      { role: 'user', content: 'Explain quantum computing in detail.' },
      { role: 'assistant', content: 'Quantum computing is a revolutionary approach...' },
      { role: 'user', content: 'How does quantum entanglement work?' },
      { role: 'assistant', content: 'Quantum entanglement is a phenomenon...' },
      { role: 'user', content: 'What are the practical applications?' }
    ]
  },

  // VS Code/Cline specific test scenarios
  clineScenarios: {
    fileCreation: [
      { 
        role: 'user', 
        content: 'Create a new JavaScript file called utils.js with helper functions for string manipulation.' 
      }
    ],
    codeReview: [
      { 
        role: 'user', 
        content: 'Review this code and suggest improvements:\n\nfunction getData() {\n  var result = fetch("/api/data").then(res => res.json());\n  return result;\n}' 
      }
    ],
    debugging: [
      { 
        role: 'user', 
        content: 'I\'m getting a "TypeError: Cannot read property \'length\' of undefined" error in my JavaScript code. Can you help me debug it?' 
      }
    ],
    refactoring: [
      { 
        role: 'user', 
        content: 'Refactor this React component to use hooks instead of class components:\n\nclass Counter extends React.Component {\n  constructor(props) {\n    super(props);\n    this.state = { count: 0 };\n  }\n\n  render() {\n    return <div>{this.state.count}</div>;\n  }\n}' 
      }
    ]
  },

  // Expected API response structures (for test validation)
  expectedResponses: {
    models: {
      object: 'list',
      data: []  // Array of model objects
    },
    chatCompletion: {
      id: 'string',
      object: 'chat.completion',
      created: 'number',
      model: 'string',
      choices: [{
        index: 'number',
        message: {
          role: 'assistant',
          content: 'string'
        },
        finish_reason: 'string'
      }]
    },
    health: {
      status: 'healthy',
      timestamp: 'string',
      components: {}
    }
  },

  // Performance test configurations
  performanceTests: {
    light: {
      requestCount: 5,
      concurrent: 2,
      maxTokens: 10
    },
    medium: {
      requestCount: 20,
      concurrent: 5,
      maxTokens: 50
    },
    heavy: {
      requestCount: 50,
      concurrent: 10,
      maxTokens: 100
    }
  },

  // Error scenarios for testing
  errorScenarios: {
    invalidModel: {
      model: 'non-existent-model',
      messages: [{ role: 'user', content: 'Test' }]
    },
    invalidRole: {
      model: 'gpt-4',
      messages: [{ role: 'invalid-role', content: 'Test' }]
    },
    missingMessages: {
      model: 'gpt-4'
    },
    emptyContent: {
      model: 'gpt-4',
      messages: [{ role: 'user', content: '' }]
    }
  },

  // Browser UI selectors
  selectors: {
    // Common elements
    body: 'body',
    title: 'h1',
    header: 'header',
    
    // React UI - Tab Navigation
    tabsList: '[role="tablist"]',
    tabLibrary: 'button[role="tab"]:contains("Model Library")',
    tabUpload: 'button[role="tab"]:contains("Upload Model")',
    tabHuggingFace: 'button[role="tab"]:contains("HuggingFace")',
    tabInfo: 'button[role="tab"]:contains("About")',
    tabContent: '[role="tabpanel"]',
    
    // Model Management
    modelCard: '[class*="ModelCard"], .card',
    modelGrid: '[class*="ModelGrid"], .grid',
    modelTitle: '.card-title',
    modelStatus: '[class*="ModelStatusIndicator"], .badge',
    loadButton: 'button:contains("Load Model")',
    unloadButton: 'button svg[class*="Pause"]',
    switchButton: 'button:contains("Switch To")',
    deleteButton: 'button svg[class*="Trash2"]',
    infoButton: 'button svg[class*="Info"]',
    
    // Search and Filter
    searchInput: 'input[placeholder*="Search models"]',
    formatFilter: 'select:has(option:contains("All Formats"))',
    capabilityFilter: 'select:has(option:contains("All Capabilities"))',
    refreshButton: 'button:contains("Refresh")',
    addModelButton: 'button:contains("Add Model")',
    
    // Drag & Drop Upload
    dropZone: '[class*="DragDropZone"], .border-dashed',
    browseButton: 'button:contains("Browse Files")',
    fileInput: 'input[type="file"]',
    uploadProgress: '.progress',
    uploadStatus: '[class*="upload-status"]',
    
    // HuggingFace Search
    hfSearchInput: 'input[placeholder*="Search HuggingFace"]',
    hfSearchButton: 'button:contains("Search")',
    hfModelCard: '[class*="ModelSearch"] .card',
    downloadButton: 'button:contains("Download Model")',
    downloadProgress: '[class*="Progress"], .progress',
    
    // Notifications
    notification: '[class*="Alert"], .alert',
    notificationTitle: '.alert-title',
    notificationDescription: '.alert-description',
    successNotification: '.border-green-200',
    errorNotification: '.border-red-200',
    infoNotification: '.border-blue-200',
    
    // WebSocket Status
    connectionStatus: 'span:contains("Connected"), span:contains("Disconnected")',
    wifiIcon: 'svg[class*="Wifi"]',
    wifiOffIcon: 'svg[class*="WifiOff"]',
    
    // Performance Metrics
    memoryUsage: 'span:contains("Memory Usage")',
    tokensPerSec: 'span:contains("tok/s")',
    loadTime: 'span:contains("load")',
    
    // Old selectors (kept for compatibility)
    modelSelector: 'select[name="model"]',
    chatInput: 'textarea[placeholder*="query"], input[placeholder*="message"]',
    sendButton: 'button[type="submit"], button:contains("Send")',
    chatResponse: '.ai-response, .response',
    statusIndicator: '.status, .health-status',
    loadingSpinner: '.loading, .spinner, .animate-spin',
    navMenu: 'nav, .navigation',
    homeLink: 'a[href="/"], a:contains("Home")',
    modelsLink: 'a[href="/models"], a:contains("Models")'
  },

  // React-specific test scenarios
  reactUIScenarios: {
    modelUpload: {
      description: 'Upload a GGUF model file',
      fileName: 'test-model.gguf',
      fileSize: 1024 * 1024 * 100, // 100MB
      expectedTab: 'library'
    },
    huggingFaceDownload: {
      description: 'Download TinyLlama from HuggingFace',
      searchQuery: 'TinyLlama',
      modelId: 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
      expectedSize: '1.1B'
    },
    modelSwitch: {
      description: 'Switch between loaded models',
      firstModel: 'tinyllama',
      secondModel: 'qwen2.5-coder'
    },
    webSocketReconnect: {
      description: 'Test WebSocket reconnection',
      disconnectTime: 5000,
      reconnectTimeout: 10000
    }
  },

  // API endpoints to test
  endpoints: {
    health: '/api/health',
    models: '/v1/models',
    chatCompletions: '/v1/chat/completions',
    completions: '/v1/completions',
    hardwareInfo: '/api/hardware/detect',
    loadedModels: '/api/models'
  },

  // Common request options
  requestOptions: {
    default: {
      timeout: 30000,
      retries: 3
    },
    streaming: {
      timeout: 60000,
      stream: true
    },
    performance: {
      timeout: 5000,
      max_tokens: 10
    }
  }
};

module.exports = { testData };
