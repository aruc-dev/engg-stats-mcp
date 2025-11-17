#!/usr/bin/env python3
"""
Validation script for Engineering Productivity MCP servers
"""
import os
import sys
import asyncio
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def validate_environment():
    """Validate environment variables"""
    print("🔍 Checking environment variables...")
    
    # Load .env file if it exists
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("✅ .env file loaded")
        except ImportError:
            print("⚠️  dotenv not available, checking system environment")
    else:
        print("⚠️  No .env file found, checking system environment")
    
    # Check GitHub config
    github_token = os.getenv("GITHUB_TOKEN")
    github_port = os.getenv("GITHUB_MCP_PORT", "4001")
    
    if github_token:
        print(f"✅ GitHub token configured (port {github_port})")
    else:
        print("❌ GITHUB_TOKEN not set")
    
    # Check Jira config
    jira_url = os.getenv("JIRA_BASE_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    jira_port = os.getenv("JIRA_MCP_PORT", "4002")
    
    if jira_url and jira_email and jira_token:
        print(f"✅ Jira configuration complete (port {jira_port})")
    else:
        missing = []
        if not jira_url: missing.append("JIRA_BASE_URL")
        if not jira_email: missing.append("JIRA_EMAIL")
        if not jira_token: missing.append("JIRA_API_TOKEN")
        print(f"❌ Jira missing: {', '.join(missing)}")
    
    # Check Confluence config
    conf_url = os.getenv("CONFLUENCE_BASE_URL")
    conf_email = os.getenv("CONFLUENCE_EMAIL")
    conf_token = os.getenv("CONFLUENCE_API_TOKEN")
    conf_port = os.getenv("CONFLUENCE_MCP_PORT", "4003")
    
    if conf_url and conf_email and conf_token:
        print(f"✅ Confluence configuration complete (port {conf_port})")
    else:
        missing = []
        if not conf_url: missing.append("CONFLUENCE_BASE_URL")
        if not conf_email: missing.append("CONFLUENCE_EMAIL")
        if not conf_token: missing.append("CONFLUENCE_API_TOKEN")
        print(f"❌ Confluence missing: {', '.join(missing)}")

async def validate_imports():
    """Check that all required modules can be imported"""
    print("\n📦 Checking Python dependencies...")
    
    required_modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("httpx", "HTTP client"),
        ("pydantic", "Pydantic"),
        ("python-dotenv", "Environment variables")
    ]
    
    all_good = True
    
    for module_name, description in required_modules:
        try:
            __import__(module_name.replace("-", "_"))
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} ({module_name}) - run: pip install {module_name}")
            all_good = False
    
    # Check MCP SDK (might not be available yet)
    try:
        import mcp
        print("✅ MCP SDK")
    except ImportError:
        print("⚠️  MCP SDK not available - servers will run with basic HTTP handling")
    
    return all_good

async def validate_project_structure():
    """Check that all required files exist"""
    print("\n📁 Checking project structure...")
    
    required_files = [
        "shared/__init__.py",
        "shared/date_utils.py",
        "shared/github_client.py", 
        "shared/jira_client.py",
        "shared/confluence_client.py",
        "mcp_github/__init__.py",
        "mcp_github/server.py",
        "mcp_jira/__init__.py",
        "mcp_jira/server.py",
        "mcp_confluence/__init__.py",
        "mcp_confluence/server.py",
        "requirements.txt",
        "README.md"
    ]
    
    all_good = True
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_good = False
    
    return all_good

def print_setup_instructions():
    """Print setup instructions"""
    print("\n🚀 Setup Instructions:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Copy .env.example to .env: cp .env.example .env")
    print("3. Edit .env with your API credentials")
    print("4. Start servers: ./start_all_servers.sh")
    print("5. Test: curl http://localhost:4001/health")

async def main():
    """Main validation function"""
    print("🔧 Engineering Productivity MCP Servers - Validation Script")
    print("=" * 60)
    
    structure_ok = await validate_project_structure()
    imports_ok = await validate_imports()
    await validate_environment()
    
    print("\n" + "=" * 60)
    
    if structure_ok and imports_ok:
        print("✅ Project setup looks good!")
        print("\n🎯 Next steps:")
        print("   1. Configure .env with your API credentials")
        print("   2. Run: ./start_all_servers.sh")
        print("   3. Test the servers with the health check endpoints")
    else:
        print("❌ Setup issues found - please fix the errors above")
        print_setup_instructions()

if __name__ == "__main__":
    asyncio.run(main())