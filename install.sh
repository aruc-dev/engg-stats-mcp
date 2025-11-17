#!/bin/bash

# Installation script for Engineering Productivity MCP servers
set -e

echo "🚀 Installing Engineering Productivity MCP Servers"
echo "=================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🔄 Activating virtual environment (venv)..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🔄 Activating virtual environment (.venv)..."
    source .venv/bin/activate
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API credentials"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
echo "🔧 Setting script permissions..."
chmod +x *.sh

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Edit .env with your API credentials"
echo "   2. Run validation: ./validate_setup.py"
echo "   3. Start servers: ./start_all_servers.sh"
echo ""
echo "📚 See README.md for detailed setup instructions"