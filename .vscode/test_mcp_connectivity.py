#!/usr/bin/env python3
"""
Test VS Code MCP Server Connectivity
Validates that MCP servers can be started with the current configuration.
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def test_python_path():
    """Test if Python path is accessible"""
    print("🔍 Testing Python Configuration...")
    
    # Test virtual environment Python
    venv_python = Path("venv/bin/python")
    if venv_python.exists():
        try:
            result = subprocess.run([str(venv_python), "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Virtual environment Python: {result.stdout.strip()}")
                return str(venv_python.absolute())
            else:
                print(f"❌ Virtual environment Python failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Virtual environment Python error: {e}")
    
    # Test system Python
    try:
        result = subprocess.run(["python3", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"⚠️  Using system Python: {result.stdout.strip()}")
            return "python3"
    except Exception as e:
        print(f"❌ System Python error: {e}")
    
    print("❌ No working Python found!")
    return None

def test_mcp_import():
    """Test if MCP modules can be imported"""
    print("\n🔍 Testing MCP Module Imports...")
    
    python_cmd = test_python_path()
    if not python_cmd:
        return False
    
    modules_to_test = [
        "mcp_github.server",
        "mcp_jira.server", 
        "mcp_confluence.server"
    ]
    
    for module in modules_to_test:
        try:
            result = subprocess.run([
                python_cmd, "-c", f"import {module}; print('✅ {module}')"
            ], capture_output=True, text=True, timeout=10, cwd=os.getcwd())
            
            if result.returncode == 0:
                print(f"✅ {module} - Import successful")
            else:
                print(f"❌ {module} - Import failed: {result.stderr.strip()}")
                return False
        except Exception as e:
            print(f"❌ {module} - Error: {e}")
            return False
    
    return True

def test_shell_scripts():
    """Test if shell scripts are executable"""
    print("\n🔍 Testing Shell Scripts...")
    
    scripts = [
        ".vscode/start_github_mcp.sh",
        ".vscode/start_jira_mcp.sh",
        ".vscode/start_confluence_mcp.sh"
    ]
    
    all_good = True
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            if os.access(script_path, os.X_OK):
                print(f"✅ {script} - Executable")
            else:
                print(f"❌ {script} - Not executable")
                all_good = False
        else:
            print(f"❌ {script} - Not found")
            all_good = False
    
    return all_good

def main():
    """Run all tests"""
    print("🚀 VS Code MCP Connectivity Test\n")
    
    print("Current directory:", os.getcwd())
    print("Virtual environment:", "✅ Found" if Path("venv").exists() else "❌ Missing")
    print(".env file:", "✅ Found" if Path(".env").exists() else "⚠️  Missing")
    
    tests = [
        test_python_path,
        test_mcp_import,
        test_shell_scripts
    ]
    
    all_passed = True
    for test in tests:
        try:
            result = test()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All MCP connectivity tests passed!")
        print("\n📝 VS Code MCP Configuration:")
        print("1. The main mcp.json should work with full Python paths")
        print("2. Alternative: Use mcp-shell.json if you have path issues")
        print("3. Restart VS Code after configuration changes")
        print("\n🔄 To apply shell-based configuration:")
        print("   cp .vscode/mcp-shell.json .vscode/mcp.json")
    else:
        print("❌ Some connectivity tests failed.")
        print("💡 Try using the shell-based configuration:")
        print("   cp .vscode/mcp-shell.json .vscode/mcp.json")
        sys.exit(1)

if __name__ == "__main__":
    main()