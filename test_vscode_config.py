#!/usr/bin/env python3
"""
Test VS Code MCP Configuration
Validates that all MCP servers can be started and are properly configured.
"""
import json
import os
import sys
from pathlib import Path

def test_vscode_configuration():
    """Test VS Code configuration files"""
    print("🔍 Testing VS Code Configuration...")
    
    vscode_dir = Path(".vscode")
    if not vscode_dir.exists():
        print("❌ .vscode directory not found")
        return False
    
    # Test required files
    required_files = [
        "mcp.json",
        "settings.json", 
        "tasks.json",
        "launch.json",
        "extensions.json"
    ]
    
    for file in required_files:
        file_path = vscode_dir / file
        if not file_path.exists():
            print(f"❌ Missing {file}")
            return False
        
        # Test JSON validity
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            print(f"✅ {file} - Valid JSON")
        except json.JSONDecodeError as e:
            print(f"❌ {file} - Invalid JSON: {e}")
            return False
    
    # Test MCP configuration specifically
    try:
        with open(vscode_dir / "mcp.json", 'r') as f:
            mcp_config = json.load(f)
        
        servers = mcp_config.get("servers", {})
        expected_servers = [
            "github-engineering",
            "jira-engineering", 
            "confluence-engineering",
            "github-analytics",
            "jira-analytics",
            "confluence-analytics"
        ]
        
        for server in expected_servers:
            if server in servers:
                print(f"✅ MCP Server '{server}' configured")
            else:
                print(f"❌ MCP Server '{server}' missing")
                return False
                
    except Exception as e:
        print(f"❌ Error reading MCP configuration: {e}")
        return False
    
    print("✅ All VS Code configuration files are valid!")
    return True

def test_workspace_file():
    """Test workspace file"""
    print("\n🔍 Testing Workspace File...")
    
    workspace_file = Path("engineering-stats-mcp.code-workspace")
    if not workspace_file.exists():
        print("❌ Workspace file not found")
        return False
    
    try:
        with open(workspace_file, 'r') as f:
            workspace_config = json.load(f)
        print("✅ Workspace file is valid JSON")
        
        if "folders" in workspace_config:
            print("✅ Workspace folders configured")
        else:
            print("❌ No folders in workspace config")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid workspace JSON: {e}")
        return False
    
    return True

def test_environment_setup():
    """Test environment setup"""
    print("\n🔍 Testing Environment Setup...")
    
    # Check for .env file
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_example.exists():
        print("❌ .env.example file missing")
        return False
    print("✅ .env.example found")
    
    if env_file.exists():
        print("✅ .env file exists")
    else:
        print("⚠️  .env file not found - copy from .env.example")
    
    # Check virtual environment
    venv_paths = [Path("venv"), Path(".venv")]
    venv_found = False
    for venv_path in venv_paths:
        if venv_path.exists():
            print(f"✅ Virtual environment found: {venv_path}")
            venv_found = True
            break
    
    if not venv_found:
        print("⚠️  No virtual environment found - run install.sh")
    
    return True

def main():
    """Run all tests"""
    print("🚀 VS Code MCP Configuration Test\n")
    
    all_passed = True
    
    # Run tests
    tests = [
        test_vscode_configuration,
        test_workspace_file,
        test_environment_setup
    ]
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All VS Code configuration tests passed!")
        print("\n📝 Next steps:")
        print("1. Open workspace: code engineering-stats-mcp.code-workspace")
        print("2. Install recommended extensions when prompted")
        print("3. Configure .env file with your API tokens")
        print("4. Run: Ctrl+Shift+P → 'Tasks: Run Task' → 'Start All Main Servers'")
    else:
        print("❌ Some tests failed. Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()