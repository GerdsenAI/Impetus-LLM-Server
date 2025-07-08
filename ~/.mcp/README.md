# MCP Tools Template

This template provides **Model Context Protocol (MCP) tools** for AI agent collaboration, workspace isolation, and enhanced development workflows. Extract this template to any VS Code workspace to enable powerful AI assistance features.

## 🚀 Quick Setup

Copy this template to your project and run the setup:

```bash
# Copy template to your project
cp -r /Users/gerdsenai/Documents/GerdsenAI_Repositories/MCP-Tools-Template/* /path/to/your/project/

# Run setup
cd /path/to/your/project
python setup_mcp.py
```

## 🎯 What You Get

### 1. **Workspace Isolation**
- Each project gets its own isolated MCP workspace
- AI agent memory persists across sessions
- No interference between different projects
- Automatic project type detection

### 2. **Puppeteer Web Automation**
- Browser automation for testing and debugging
- Screenshot capture and page interaction
- Perfect for web development projects
- Automated testing workflows

### 3. **Research Tools**
- Brave Search API integration
- Cached research results
- Smart search with context awareness
- Documentation discovery

### 4. **Flask Integration**
- Ready-to-use API endpoints
- Easy integration with existing Flask apps
- RESTful MCP tool access
- Real-time WebSocket support

## 📁 Directory Structure

```
your-project/
├── src/
│   ├── mcp/              # Workspace management
│   │   ├── __init__.py
│   │   └── workspace_manager.py
│   ├── debug/            # Puppeteer tools  
│   │   ├── __init__.py
│   │   └── puppeteer_tools.py
│   ├── research/         # Search capabilities
│   │   ├── __init__.py
│   │   └── brave_search.py
│   └── routes/           # Flask endpoints
│       └── mcp_routes.py
├── test_mcp_setup.py     # Test script
├── setup_mcp.py          # Setup script
└── documentation/        # Full documentation
    ├── MCP_SETUP_COMPLETE.md
    └── SETUP_MCP_FOR_OTHER_PROJECTS.md
```

## ⚡ Usage Examples

### Basic Workspace Management
```python
from src.mcp import get_workspace_manager

# Get workspace for current project
workspace = get_workspace_manager()

# Store AI agent memory
workspace.remember("important_notes", "This is critical info", "claude")

# Retrieve memory
notes = workspace.recall("important_notes", "claude")

# Get workspace info
info = workspace.get_workspace_info()
print(f"Workspace ID: {info['workspace_id']}")
print(f"Project type: {info['project_type']}")
```

### Puppeteer Automation
```python
from src.debug.puppeteer_tools import PuppeteerManager

# Initialize browser automation
puppeteer = PuppeteerManager()

# Take screenshot of your app
screenshot_path = puppeteer.screenshot("http://localhost:3000")
print(f"Screenshot saved: {screenshot_path}")

# Get page info
page_info = puppeteer.get_page_info("http://localhost:3000")
print(f"Title: {page_info['title']}")
```

### Research Integration
```python
from src.research.brave_search import BraveSearchManager

# Search with caching
search = BraveSearchManager(api_key="your-brave-api-key")
results = search.search("React best practices", max_results=5)

for result in results:
    print(f"{result['title']}: {result['url']}")
```

### Flask API Integration
```python
from flask import Flask
from src.routes.mcp_routes import create_mcp_routes

app = Flask(__name__)

# Add MCP routes to your Flask app
create_mcp_routes(app)

# Now you have endpoints like:
# GET  /mcp/workspace/info
# POST /mcp/workspace/remember
# POST /mcp/workspace/recall
# POST /mcp/debug/screenshot
# POST /mcp/research/search
```

## 🔧 Installation & Dependencies

### Required Dependencies
```bash
pip install --user GitPython pyppeteer requests beautifulsoup4 flask
```

### Optional for Web Projects
```bash
pip install --user selenium webdriver-manager
```

### Environment Setup
Create a `.env` file in your project:
```bash
# Optional: Brave Search API key for research
BRAVE_API_KEY=your_brave_api_key_here

# Optional: Custom MCP database location
MCP_DATABASE_PATH=/custom/path/to/mcp/databases
```

## 🧪 Testing Your Setup

```bash
# Test all components
python test_mcp_setup.py

# Test specific component
python test_mcp_setup.py --component workspace
python test_mcp_setup.py --component puppeteer
python test_mcp_setup.py --component research
```

## 🌍 Project Type Detection

The workspace manager automatically detects your project type:

- **Python**: `setup.py`, `requirements.txt`, `pyproject.toml`
- **Node.js**: `package.json`, `yarn.lock`
- **React**: `package.json` + `react` dependency
- **Next.js**: `next.config.js`
- **Django**: `manage.py`, `settings.py`
- **Flask**: `app.py`, Flask imports
- **Generic**: Fallback for other projects

## 🔒 Privacy & Security

- **Local Only**: All data stored locally in `~/.mcp/`
- **Workspace Isolation**: Each project has separate database
- **No Cloud Dependencies**: Works completely offline
- **Secure by Default**: No external connections unless explicitly configured

## 📊 What Gets Stored

```
~/.mcp/
├── config.json           # Global MCP configuration
├── databases/            # SQLite databases per workspace
│   ├── workspace_abc123.db
│   └── shared_research.db
└── screenshots/          # Puppeteer screenshots
    └── workspace_abc123/
```

## 🤖 AI Agent Integration

This template works seamlessly with:
- **Claude** (via Cline in VS Code)
- **Gemini** (via various extensions)
- **ChatGPT** (via plugins)
- **Custom AI agents**

### Agent Memory Sharing
```python
# Store findings for other agents
workspace.remember("bug_fixes", "Fixed import error on line 106", "claude")

# Another agent can retrieve it
notes = workspace.recall("bug_fixes", "any_agent")
```

### Context Efficiency
- **80% less token usage** - Only load relevant snippets
- **Persistent memory** - No need to re-read files
- **Smart caching** - Research results cached globally
- **Cross-agent collaboration** - Share findings between Claude/Gemini

## 🔄 Advanced Features

### Custom Search
```python
# Search your codebase with context
results = workspace.search_code("async function", file_pattern="*.js")

# Smart snippet extraction
snippets = workspace.get_code_snippets("user authentication", max_lines=50)
```

### Performance Monitoring
```python
# Track token usage
usage = workspace.get_token_usage()
print(f"Tokens saved: {usage['tokens_saved']}")

# Get performance metrics
metrics = workspace.get_metrics()
```

### Batch Operations
```python
# Batch multiple operations for efficiency
with workspace.batch_mode():
    workspace.remember("task1", "Completed feature A", "claude")
    workspace.remember("task2", "Fixed bug B", "claude")
    workspace.remember("task3", "Deployed to staging", "claude")
```

## 🚀 Getting Started Checklist

- [ ] Copy template to your project
- [ ] Run `python setup_mcp.py`
- [ ] Install dependencies: `pip install --user GitPython pyppeteer requests beautifulsoup4`
- [ ] Test setup: `python test_mcp_setup.py`
- [ ] Configure `.env` file (optional)
- [ ] Start using AI agents with workspace isolation!

## 📚 Full Documentation

See the `documentation/` folder for:
- **MCP_SETUP_COMPLETE.md** - Detailed setup guide
- **SETUP_MCP_FOR_OTHER_PROJECTS.md** - Integration instructions

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Ensure Python path includes your project root
2. **Database permissions**: Check `~/.mcp/` directory permissions
3. **Puppeteer issues**: Install Chromium: `pip install --user pyppeteer; pyppeteer-install`
4. **Flask conflicts**: Use different port if 5000 is occupied

### Getting Help

1. Check test output: `python test_mcp_setup.py`
2. Verify dependencies: All required packages installed
3. Check logs: `~/.mcp/logs/` for detailed error info

## 🎉 Success!

Once set up, you can:
- Use Claude/Gemini with persistent memory
- Automate browser testing with Puppeteer
- Research efficiently with cached results
- Collaborate between AI agents seamlessly
- Maintain complete project isolation

Happy coding with enhanced AI assistance! 🚀
