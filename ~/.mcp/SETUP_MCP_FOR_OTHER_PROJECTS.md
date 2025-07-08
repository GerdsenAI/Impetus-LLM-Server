# Setting Up MCP Tools in Other Projects

This guide shows how to add the MCP (Model Context Protocol) tools to any other VS Code workspace or project.

## Quick Setup (2 minutes)

### Option 1: Copy the MCP Files 

1. **Copy the MCP modules to your other project**:
```bash
# Navigate to your other project
cd /path/to/your/other/project

# Create the directory structure
mkdir -p src/mcp src/debug src/research src/routes

# Copy the MCP files from Impetus project
cp /Users/gerdsenai/Documents/GerdsenAI_Repositories/Impetus-LLM-Server/gerdsen_ai_server/src/mcp/* src/mcp/
cp /Users/gerdsenai/Documents/GerdsenAI_Repositories/Impetus-LLM-Server/gerdsen_ai_server/src/debug/* src/debug/
cp /Users/gerdsenai/Documents/GerdsenAI_Repositories/Impetus-LLM-Server/gerdsen_ai_server/src/research/* src/research/
cp /Users/gerdsenai/Documents/GerdsenAI_Repositories/Impetus-LLM-Server/gerdsen_ai_server/src/routes/mcp_routes.py src/routes/

# Copy the test script
cp /Users/gerdsenai/Documents/GerdsenAI_Repositories/Impetus-LLM-Server/test_mcp_setup.py .
```

2. **The shared config is already global** (`~/.mcp/config.json`) - no need to copy

3. **Test the setup**:
```bash
python test_mcp_setup.py
```

### Option 2: Use the Setup Script (Easier)

I'll create a setup script you can run in any project:

```bash
# In your other project directory
curl -o setup_mcp.py https://raw.githubusercontent.com/.../setup_mcp.py  # (I'll create this below)
python setup_mcp.py
```

## How It Works Automatically

The beautiful thing about this MCP system is that **each project gets its own isolated workspace automatically**:

### Automatic Project Detection
When you use MCP tools in your other project, the system will:

1. **Detect the new workspace** based on:
   - Git repository (if different from Impetus)
   - Directory name and path
   - VS Code workspace files
   - Project type (Python, JavaScript, etc.)

2. **Create a new isolated database**:
   ```
   ~/.mcp/databases/
   ├── workspace_96affea29ec13795.db    # Impetus LLM Server
   ├── workspace_a1b2c3d4e5f6g7h8.db    # Your other project (NEW)
   └── shared_research.db               # Shared research cache
   ```

3. **Maintain complete isolation**:
   - Your other project's AI agent memory is completely separate
   - No interference with Impetus project data
   - Each project maintains its own context and memory

### Usage in Your Other Project

Once copied, you can use MCP tools exactly the same way:

```python
# This will automatically create a NEW workspace for your other project
from src.mcp import get_workspace_manager

workspace = get_workspace_manager()
info = workspace.get_workspace_info()
print(f"Working in: {info['project_type']} project")
print(f"Workspace ID: {info['workspace_id']}")  # Will be different from Impetus!

# Store memory specific to this project
workspace.remember("project_notes", "This is my other project", "claude", "normal")
```

## If You Have a Flask/Web Server

If your other project has a Flask server, add the MCP routes:

```python
# In your main Flask app
from src.routes.mcp_routes import mcp_bp

app.register_blueprint(mcp_bp)  # Adds /mcp/* endpoints
```

## Environment Setup for Other Projects

1. **Copy environment template**:
```bash
cp /Users/gerdsenai/Documents/GerdsenAI_Repositories/Impetus-LLM-Server/.env.example .env
```

2. **Install dependencies** (same for all projects):
```bash
pip install --user GitPython pyppeteer requests beautifulsoup4
```

## Directory Structure in Your Other Project

After setup, your other project will have:
```
your-other-project/
├── src/
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── workspace_manager.py
│   ├── debug/
│   │   ├── __init__.py
│   │   └── puppeteer_tools.py
│   ├── research/
│   │   ├── __init__.py
│   │   └── brave_search.py
│   └── routes/
│       └── mcp_routes.py
├── test_mcp_setup.py
└── .env
```

## What Gets Shared vs Isolated

### ✅ Shared Across All Projects:
- Global configuration (`~/.mcp/config.json`)
- Research cache (saves API calls)
- Screenshot directory structure
- Dependencies installation

### 🔒 Isolated Per Project:
- Workspace databases
- AI agent memory
- Project-specific context
- Session history
- Local file operations

## Testing Multiple Projects

You can test that isolation works:

1. **In Impetus project**:
```python
from gerdsen_ai_server.src.mcp import get_workspace_manager
workspace = get_workspace_manager()
workspace.remember("test", "impetus project data", "claude")
print(f"Impetus workspace: {workspace.workspace_id}")
```

2. **In your other project**:
```python
from src.mcp import get_workspace_manager
workspace = get_workspace_manager()
workspace.remember("test", "other project data", "claude")
print(f"Other workspace: {workspace.workspace_id}")
```

3. **Verify isolation**:
```python
# In Impetus: recall will return "impetus project data"
# In other project: recall will return "other project data"
# They're completely isolated!
```

## Quick Verification

After setup, run in your other project:
```bash
python test_mcp_setup.py
```

You should see:
```
✅ Workspace detected: [different ID from Impetus]
   Project type: [detected type]
   Root path: [your other project path]
```

The workspace ID will be different, confirming isolation is working!
