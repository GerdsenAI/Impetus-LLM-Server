#!/usr/bin/env python3
"""
MCP Tools Setup Script
Automatically sets up MCP (Model Context Protocol) tools in any project
"""

import os
import sys
import shutil
import json
from pathlib import Path

def setup_mcp_tools():
    """Setup MCP tools in the current directory"""
    
    print("🔧 Setting up MCP Tools for this project...")
    print("=" * 50)
    
    # Get current directory and source paths
    current_dir = Path.cwd()
    
    # Try to find the Impetus source (adjust path as needed)
    possible_impetus_paths = [
        Path.home() / "Documents/GerdsenAI_Repositories/Impetus-LLM-Server",
        Path.home() / "Desktop/Impetus-LLM-Server",
        Path("/Users/gerdsenai/Documents/GerdsenAI_Repositories/Impetus-LLM-Server"),
        # Add current directory in case we're running from Impetus
        Path(__file__).parent
    ]
    
    impetus_src = None
    for path in possible_impetus_paths:
        if (path / "gerdsen_ai_server" / "src" / "mcp").exists():
            impetus_src = path / "gerdsen_ai_server" / "src"
            break
    
    if not impetus_src:
        print("❌ Could not find Impetus source directory.")
        print("\nManual setup required:")
        print("1. Locate your Impetus-LLM-Server directory")
        print("2. Copy the instructions from SETUP_MCP_FOR_OTHER_PROJECTS.md")
        return False
    
    print(f"✅ Found Impetus source: {impetus_src}")
    
    # Create directory structure
    directories = ["src/mcp", "src/debug", "src/research", "src/routes"]
    
    for dir_path in directories:
        target_dir = current_dir / dir_path
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")
    
    # Copy MCP files
    files_to_copy = [
        ("mcp/__init__.py", "src/mcp/__init__.py"),
        ("mcp/workspace_manager.py", "src/mcp/workspace_manager.py"),
        ("debug/__init__.py", "src/debug/__init__.py"),
        ("debug/puppeteer_tools.py", "src/debug/puppeteer_tools.py"),
        ("research/__init__.py", "src/research/__init__.py"),
        ("research/brave_search.py", "src/research/brave_search.py"),
        ("routes/mcp_routes.py", "src/routes/mcp_routes.py"),
    ]
    
    for src_file, dst_file in files_to_copy:
        src_path = impetus_src / src_file
        dst_path = current_dir / dst_file
        
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"📄 Copied: {src_file} -> {dst_file}")
        else:
            print(f"⚠️  Warning: {src_file} not found")
    
    # Copy test script
    test_script_src = impetus_src.parent.parent / "test_mcp_setup.py"
    test_script_dst = current_dir / "test_mcp_setup.py"
    
    if test_script_src.exists():
        shutil.copy2(test_script_src, test_script_dst)
        print(f"📄 Copied: test_mcp_setup.py")
    
    # Copy .env.example if it doesn't exist
    env_example_src = impetus_src.parent.parent / ".env.example"
    env_example_dst = current_dir / ".env.example"
    
    if env_example_src.exists() and not env_example_dst.exists():
        shutil.copy2(env_example_src, env_example_dst)
        print(f"📄 Copied: .env.example")
    
    # Check for global MCP config
    global_config = Path.home() / ".mcp" / "config.json"
    if global_config.exists():
        print(f"✅ Global MCP config found: {global_config}")
    else:
        print(f"⚠️  Global MCP config not found. Run this in Impetus project first.")
    
    # Create a simple project-specific config
    project_config = {
        "project_name": current_dir.name,
        "setup_date": str(Path.cwd()),
        "mcp_version": "1.0.0",
        "auto_setup": True
    }
    
    config_file = current_dir / "mcp_config.json"
    with open(config_file, 'w') as f:
        json.dump(project_config, f, indent=2)
    print(f"📄 Created: mcp_config.json")
    
    print("\n" + "=" * 50)
    print("✅ MCP Tools setup complete!")
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install --user GitPython pyppeteer requests beautifulsoup4")
    print("2. Test the setup: python test_mcp_setup.py")
    print("3. Copy .env.example to .env and configure if needed")
    
    print("\n🔍 Usage example:")
    print("""
# In your Python code:
from src.mcp import get_workspace_manager

workspace = get_workspace_manager()
workspace.remember("notes", "This is my project", "claude")
info = workspace.get_workspace_info()
print(f"Project type: {info['project_type']}")
print(f"Workspace ID: {info['workspace_id']}")
""")
    
    print("\n🎯 What you get:")
    print("- Isolated workspace (won't interfere with other projects)")
    print("- Persistent AI agent memory")
    print("- Puppeteer web automation tools")
    print("- Research capabilities with caching")
    print("- Flask endpoints (if you have a Flask server)")
    
    return True

def test_setup():
    """Test that the MCP setup works"""
    print("\n🧪 Testing MCP setup...")
    
    try:
        # Test imports
        sys.path.insert(0, str(Path.cwd()))
        
        from src.mcp import get_workspace_manager
        workspace = get_workspace_manager()
        
        info = workspace.get_workspace_info()
        print(f"✅ Workspace detected: {info['workspace_id']}")
        print(f"   Project type: {info['project_type']}")
        print(f"   Root path: {info['root_path']}")
        
        # Test memory
        workspace.remember("setup_test", "MCP setup successful", "claude")
        data = workspace.recall("setup_test", "claude")
        
        if data == "MCP setup successful":
            print("✅ Memory storage/retrieval working")
            return True
        else:
            print("❌ Memory test failed")
            return False
            
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("MCP Tools Setup Script")
    print("Setting up workspace isolation and AI tools...")
    print("")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Just test existing setup
        return test_setup()
    
    # Check if we're in the Impetus directory
    if "Impetus-LLM-Server" in str(Path.cwd()):
        print("⚠️  You're in the Impetus project directory.")
        print("Run this script in your OTHER project directory.")
        print("")
        
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return False
    
    # Run setup
    success = setup_mcp_tools()
    
    if success:
        print("\n🎉 Setup complete! MCP tools are ready to use.")
        
        # Offer to run test
        response = input("\nRun test to verify setup? (Y/n): ").lower()
        if response != 'n':
            test_setup()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
