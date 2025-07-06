# MCP Development Workflow - Impetus-LLM-Server

This document provides comprehensive workflows for using MCP tools in the Impetus-LLM-Server project, prioritizing automated testing with Puppeteer and cross-agent collaboration.

## 🎯 Quick Start: MCP-First Development

### 1. Agent Initialization (30 seconds)
```bash
# MANDATORY: Use MCP tools for context loading (80% token reduction)
1. use_mcp_tool("impetus-system-monitor", "get_system_overview", {})
2. use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "read_graph", {})
3. use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/git", "git_status", {})
4. use_mcp_tool("impetus-filesystem-manager", "scan_models", {"directory": "/Users/gerdsenai/Models"})

# OPTIONAL: Only if MCP fails
# Read .clinerules/memory.md for fallback context
```

### 2. Automated Testing First (PRIMARY VALIDATION METHOD)
```bash
# Test API endpoints with Puppeteer
use_mcp_tool("github.com/modelcontextprotocol/servers-archived/tree/main/src/puppeteer", "puppeteer_navigate", {
    "url": "http://localhost:8080/v1/models"
})

# Take screenshot for documentation
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "takeScreenshot", {})

# Performance audit
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "runPerformanceAudit", {})
```

### 3. Cross-Agent Collaboration
```bash
# Share findings with other agents (Claude/Gemini)
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "create_entities", {
    "entities": [{
        "name": "session_progress",
        "entityType": "development_session",
        "observations": ["Completed feature X", "Next: implement Y"]
    }]
})

# Check previous agent work
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "search_nodes", {
    "query": "claude OR gemini recent work"
})
```

## 🚨 PRIORITY: Puppeteer-First Testing Workflows

### Testing API Endpoints
```bash
# 1. Navigate to API endpoint
use_mcp_tool("github.com/modelcontextprotocol/servers-archived/tree/main/src/puppeteer", "puppeteer_navigate", {
    "url": "http://localhost:8080/v1/models"
})

# 2. Capture response
use_mcp_tool("github.com/modelcontextprotocol/servers-archived/tree/main/src/puppeteer", "puppeteer_evaluate", {
    "script": "document.body.innerText"
})

# 3. Screenshot for documentation
use_mcp_tool("github.com/modelcontextprotocol/servers-archived/tree/main/src/puppeteer", "puppeteer_screenshot", {
    "name": "api_models_endpoint"
})
```

### Testing Frontend Components
```bash
# Navigate to React app
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_navigate", {
    "url": "http://localhost:3000",
    "browserType": "chromium"
})

# Test model management UI
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_click", {
    "selector": "[data-testid='model-upload-button']"
})

# Capture UI state
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_screenshot", {
    "name": "model_management_ui",
    "fullPage": true
})
```

### Performance Monitoring
```bash
# Run comprehensive performance audit
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "runPerformanceAudit", {})

# Check accessibility
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "runAccessibilityAudit", {})

# Monitor console errors
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "getConsoleErrors", {})
```

## 🔧 Development Task Workflows

### 1. Feature Implementation Workflow

#### Step 1: Research & Planning
```bash
# Search for implementation patterns
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/brave-search", "brave_web_search", {
    "query": "React drag drop file upload best practices",
    "count": 5
})

# Get documentation context
use_mcp_tool("github.com/upstash/context7-mcp", "resolve-library-id", {
    "libraryName": "react-dropzone"
})

# Sequential thinking for complex problems
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking", "sequentialthinking", {
    "thought": "Need to implement drag & drop for model files",
    "nextThoughtNeeded": true,
    "thoughtNumber": 1,
    "totalThoughts": 5
})
```

#### Step 2: Code Implementation
```bash
# Read existing code
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "read_file", {
    "path": "gerdsen-ai-frontend/src/components/DragDropZone.jsx"
})

# Write new code
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "write_file", {
    "path": "gerdsen-ai-frontend/src/components/ModelUploader.jsx",
    "content": "// New component implementation..."
})
```

#### Step 3: Testing & Validation
```bash
# Test the new component
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_navigate", {
    "url": "http://localhost:3000/models"
})

# Validate drag & drop functionality
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_upload_file", {
    "selector": "[data-testid='file-upload']",
    "filePath": "/Users/gerdsenai/Models/test-model.gguf"
})

# Screenshot the result
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "takeScreenshot", {})
```

#### Step 4: Documentation & Commit
```bash
# Update memory with progress
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "add_observations", {
    "observations": [{
        "entityName": "model_uploader_component",
        "contents": ["Implemented drag & drop", "Added file validation", "Tests passing"]
    }]
})

# Commit changes
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/git", "git_add", {
    "files": ["gerdsen-ai-frontend/src/components/ModelUploader.jsx"]
})

use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/git", "git_commit", {
    "message": "feat: Add drag & drop model uploader component\n\n- Implement file validation\n- Add progress indicators\n- Include accessibility features"
})
```

### 2. Bug Fix Workflow

#### Step 1: Investigate Issue
```bash
# Check system status
use_mcp_tool("impetus-system-monitor", "get_system_overview", {})

# Look for error patterns
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "search_files", {
    "path": "gerdsen_ai_server/src",
    "pattern": "error|exception|traceback",
    "excludePatterns": ["*.pyc", "__pycache__"]
})

# Check console logs
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "getConsoleErrors", {})
```

#### Step 2: Test Reproduction
```bash
# Navigate to problematic area
use_mcp_tool("github.com/modelcontextprotocol/servers-archived/tree/main/src/puppeteer", "puppeteer_navigate", {
    "url": "http://localhost:8080/api/models/upload"
})

# Try to reproduce the bug
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_fill", {
    "selector": "#model-path",
    "value": "/path/to/broken/model.gguf"
})

# Capture error state
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_console_logs", {
    "type": "error"
})
```

#### Step 3: Fix & Validate
```bash
# Apply the fix
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "edit_file", {
    "path": "gerdsen_ai_server/src/integrated_mlx_manager.py",
    "edits": [{
        "oldText": "AppleFrameworksIntegration()",
        "newText": "EnhancedAppleFrameworksIntegration()"
    }],
    "dryRun": false
})

# Test the fix
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_navigate", {
    "url": "http://localhost:8080/v1/models"
})

# Verify no errors
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "getConsoleErrors", {})
```

### 3. Performance Optimization Workflow

#### Step 1: Baseline Measurement
```bash
# Get current system performance
use_mcp_tool("impetus-system-monitor", "monitor_performance", {
    "duration_seconds": 60,
    "interval_seconds": 5
})

# Run performance audit
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "runPerformanceAudit", {})

# Check thermal throttling
use_mcp_tool("impetus-system-monitor", "check_thermal_throttling", {})
```

#### Step 2: Identify Bottlenecks
```bash
# Analyze model loading performance
use_mcp_tool("impetus-filesystem-manager", "validate_model", {
    "filepath": "/Users/gerdsenai/Models/qwen2.5-coder-32b-instruct-q4_0.gguf"
})

# Get optimization recommendations
use_mcp_tool("impetus-system-monitor", "optimize_for_model", {
    "model_size_gb": 17.36,
    "target_performance": "max_performance"
})
```

#### Step 3: Apply Optimizations
```bash
# Update configuration based on recommendations
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "edit_file", {
    "path": "gerdsen_ai_server/src/config/optimization.py",
    "edits": [{
        "oldText": "memory_allocation = 0.5",
        "newText": "memory_allocation = dynamic_calculation()"
    }]
})

# Test performance improvement
use_mcp_tool("impetus-system-monitor", "estimate_model_performance", {
    "model_size_gb": 17.36,
    "model_format": "gguf"
})
```

## 🤝 Cross-Agent Collaboration Patterns

### Claude → Gemini Handoff
```bash
# Claude saves session summary
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "create_entities", {
    "entities": [{
        "name": "claude_session_2025_07_06",
        "entityType": "development_session",
        "observations": [
            "Updated ai.md with MCP workflows",
            "Enhanced memory.md with 18 MCP servers",
            "Next: Create MCP development workflow guide",
            "Priority: Puppeteer testing integration"
        ]
    }]
})

# Add session context
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "add_observations", {
    "observations": [{
        "entityName": "project_state",
        "contents": [
            "MVP 100% complete with real inference",
            "18 MCP servers configured and tested",
            "Puppeteer priority for all testing",
            "Cross-agent collaboration active"
        ]
    }]
})
```

### Gemini Session Start
```bash
# Load Claude's work
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "search_nodes", {
    "query": "claude_session_2025_07_06"
})

# Get project state
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "open_nodes", {
    "names": ["project_state", "development_priorities"]
})

# Continue seamlessly
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/git", "git_status", {})
```

## 📊 Research & Documentation Workflows

### Technical Research
```bash
# Search for implementation patterns
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/brave-search", "brave_web_search", {
    "query": "Apple Silicon MLX performance optimization M3 Ultra",
    "count": 10
})

# Get specific documentation
use_mcp_tool("github.com/zcaceres/fetch-mcp", "fetch_markdown", {
    "url": "https://ml-explore.github.io/mlx/build/html/install.html"
})

# Store findings
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "create_entities", {
    "entities": [{
        "name": "mlx_optimization_research",
        "entityType": "research_findings",
        "observations": ["Found Metal shader optimizations", "Discovered quantization techniques"]
    }]
})
```

### Code Documentation
```bash
# Generate documentation for complex functions
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "read_file", {
    "path": "gerdsen_ai_server/src/model_loaders/gguf_loader.py"
})

# Create comprehensive documentation
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "write_file", {
    "path": "docs/model_loaders/gguf_loader_guide.md",
    "content": "# GGUF Model Loader Guide\n\n## Overview\n..."
})
```

## 🔄 Continuous Integration Workflows

### Pre-Commit Testing
```bash
# Run all tests before commit
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_navigate", {
    "url": "http://localhost:8080/v1/models"
})

use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "runPerformanceAudit", {})

use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "runAccessibilityAudit", {})

# Only commit if all tests pass
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/git", "git_commit", {
    "message": "feat: Implement feature with full test coverage"
})
```

### Post-Deploy Validation
```bash
# Validate deployment
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_navigate", {
    "url": "http://localhost:8080/health"
})

# Check system resources
use_mcp_tool("impetus-system-monitor", "get_system_overview", {})

# Document deployment status
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/memory", "add_observations", {
    "observations": [{
        "entityName": "deployment_status",
        "contents": ["Deployment successful", "All health checks passing", "Performance optimal"]
    }]
})
```

## 🎯 Priority Guidelines for All Agents

### 1. Always Start with MCP Tools
- **Context Loading**: Use MCP memory/filesystem instead of reading large files
- **System Status**: Check with system monitor before making changes
- **Testing**: Use Puppeteer/Playwright for all validation

### 2. Puppeteer Testing is Mandatory
- **API Testing**: Every endpoint must be tested with Puppeteer
- **UI Testing**: All frontend changes require screenshot validation
- **Performance**: Regular performance audits with Browser Tools MCP

### 3. Cross-Agent Collaboration
- **Share Findings**: Always update memory graph with important discoveries
- **Context Handoff**: Leave detailed session summaries for other agents
- **Avoid Duplication**: Check memory before starting research

### 4. Documentation Through MCP
- **Screenshot Everything**: Use automated screenshot capture
- **Research Cache**: Store all findings in Brave Search cache
- **Knowledge Graph**: Build persistent project knowledge

## 🚀 Advanced MCP Workflows

### Model Performance Analysis
```bash
# Comprehensive model analysis
use_mcp_tool("impetus-filesystem-manager", "scan_models", {
    "directory": "/Users/gerdsenai/Models"
})

use_mcp_tool("impetus-system-monitor", "estimate_model_performance", {
    "model_size_gb": 17.36,
    "model_format": "gguf"
})

# Find optimal models for current hardware
use_mcp_tool("impetus-filesystem-manager", "organize_models", {
    "directory": "/Users/gerdsenai/Models"
})
```

### Automated UI Development
```bash
# Research component patterns
use_mcp_tool("github.com/21st-dev/magic-mcp", "21st_magic_component_inspiration", {
    "message": "Need a model selection dropdown",
    "searchQuery": "dropdown select"
})

# Test component implementation
use_mcp_tool("github.com/executeautomation/mcp-playwright", "playwright_click", {
    "selector": "[data-testid='model-selector']"
})

# Validate accessibility
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "runAccessibilityAudit", {})
```

### Intelligent Code Generation
```bash
# Use sequential thinking for complex logic
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking", "sequentialthinking", {
    "thought": "Need to optimize model loading for M3 Ultra with 60 GPU cores",
    "nextThoughtNeeded": true,
    "thoughtNumber": 1,
    "totalThoughts": 8
})

# Research best practices
use_mcp_tool("github.com/upstash/context7-mcp", "get-library-docs", {
    "context7CompatibleLibraryID": "/apple/mlx",
    "topic": "gpu acceleration"
})
```

## 🎖️ Best Practices

1. **MCP First**: Always try MCP tools before reading files directly
2. **Test Early**: Use Puppeteer for immediate validation
3. **Share Knowledge**: Update memory graph with every session
4. **Document Visually**: Screenshots are worth a thousand words
5. **Optimize Automatically**: Let system monitor guide performance decisions
6. **Collaborate Seamlessly**: Use memory graph for agent handoffs
7. **Research Smart**: Cache everything in Brave Search
8. **Think Sequentially**: Use sequential thinking for complex problems

## 🔧 Troubleshooting

### MCP Tools Not Working
```bash
# Check MCP server status
use_mcp_tool("github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "list_allowed_directories", {})

# Test basic functionality
use_mcp_tool("impetus-system-monitor", "get_system_overview", {})
```

### Puppeteer Failures
```bash
# Check browser status
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "getConsoleLogs", {})

# Wipe logs and retry
use_mcp_tool("github.com/AgentDeskAI/browser-tools-mcp", "wipeLogs", {})
```

### Performance Issues
```bash
# Monitor thermal state
use_mcp_tool("impetus-system-monitor", "check_thermal_throttling", {})

# Get optimization recommendations
use_mcp_tool("impetus-system-monitor", "optimize_for_model", {
    "model_size_gb": 17.36,
    "target_performance": "balanced"
})
```

This workflow guide ensures all agents (Claude, Gemini, etc.) can work efficiently with the comprehensive MCP toolset, prioritizing automated testing and seamless collaboration while achieving 80%+ token reduction through smart context management.
