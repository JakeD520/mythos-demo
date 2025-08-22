#!/bin/bash
# MythOS Demo - Quick Start Script (Linux/Mac)

echo "========================================"
echo "    MythOS Demo - Quick Start Script"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ Python detected: $(python3 --version)"

echo
echo "[1/4] Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo
echo "[2/4] Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"

echo
echo "[3/4] Starting Island Scorer service..."
echo "Starting on http://localhost:8000"
echo "Press Ctrl+C to stop the service"
echo
echo "⚡ MythOS Demo is starting..."
echo "🌍 Available worlds: Greek Mythology, Fantasy Realm, Vampire Cyberpunk"
echo "🎪 Demo will be ready in ~30 seconds (loading AI models)"
echo
echo "💡 To use the demo:"
echo "   1. Wait for 'Application startup complete' message"
echo "   2. Open working_demo.html in your browser"
echo "   3. Or visit: file://$(pwd)/working_demo.html"
echo
echo "⚠️  Press Ctrl+C to stop the service"
echo "----------------------------------------"

# Auto-open demo after delay (if on macOS/Linux with GUI)
(sleep 35 && if command -v open &> /dev/null; then open "working_demo.html"; elif command -v xdg-open &> /dev/null; then xdg-open "working_demo.html"; fi) &

# Start the service
python -m services.island_scorer.app

echo
echo "[4/4] Service stopped."
