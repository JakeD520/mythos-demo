#!/usr/bin/env python3
"""
MythOS Demo - Cross-Platform Quick Start Script
Automatically sets up environment and starts the demo
"""

import os
import sys
import subprocess
import platform
import time
import webbrowser
from pathlib import Path

def run_command(cmd, shell=False, check=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except Exception as e:
        return False, "", str(e)

def print_step(step, total, message):
    """Print a formatted step message"""
    print(f"\n[{step}/{total}] {message}")

def print_status(success, message):
    """Print status with emoji"""
    status = "✅" if success else "❌"
    print(f"{status} {message}")

def main():
    print("=" * 50)
    print("    MythOS Demo - Quick Start Script")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required. Current version:", sys.version)
        return False
    
    print_status(True, f"Python {sys.version.split()[0]} detected")
    
    # Determine platform-specific commands
    is_windows = platform.system() == "Windows"
    venv_python = "venv\\Scripts\\python.exe" if is_windows else "venv/bin/python"
    venv_pip = "venv\\Scripts\\pip.exe" if is_windows else "venv/bin/pip"
    activate_cmd = "venv\\Scripts\\activate.bat" if is_windows else "source venv/bin/activate"
    
    # Step 1: Create virtual environment
    print_step(1, 4, "Setting up virtual environment...")
    
    if not os.path.exists("venv"):
        success, stdout, stderr = run_command([sys.executable, "-m", "venv", "venv"])
        print_status(success, "Virtual environment created" if success else "Failed to create venv")
        if not success:
            print(f"Error: {stderr}")
            return False
    else:
        print_status(True, "Virtual environment already exists")
    
    # Step 2: Install dependencies
    print_step(2, 4, "Installing dependencies...")
    
    if os.path.exists("requirements.txt"):
        success, stdout, stderr = run_command([venv_pip, "install", "-r", "requirements.txt"])
        print_status(success, "Dependencies installed" if success else "Failed to install dependencies")
        if not success:
            print(f"Error: {stderr}")
            return False
    else:
        print_status(False, "requirements.txt not found")
        return False
    
    # Step 3: Check for required files
    print_step(3, 4, "Checking demo files...")
    
    required_files = [
        "services/island_scorer/app.py",
        "working_demo.html",
        "worlds/greek_myth.index",
        "corpus/greek_myth"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        print_status(exists, f"Found {file_path}" if exists else f"Missing {file_path}")
        if not exists:
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ Some required files are missing. Please ensure you have the complete repository.")
        return False
    
    # Step 4: Start the service
    print_step(4, 4, "Starting MythOS Demo...")
    print()
    print("🚀 Starting Island Scorer service on http://localhost:8000")
    print("🌍 Available worlds: Greek Mythology, Fantasy Realm, Vampire Cyberpunk")
    print("🎪 Demo will be ready in ~30 seconds (loading AI models)")
    print()
    print("💡 To use the demo:")
    print("   1. Wait for 'Application startup complete' message")
    print("   2. Open working_demo.html in your browser")
    print("   3. Or visit: file://" + str(Path.cwd() / "working_demo.html"))
    print()
    print("⚠️  Press Ctrl+C to stop the service")
    print("-" * 50)
    
    # Auto-open demo after a delay
    def open_demo():
        time.sleep(35)  # Wait for service to fully start
        demo_path = Path.cwd() / "working_demo.html"
        try:
            webbrowser.open(f"file://{demo_path}")
            print(f"\n🎪 Demo opened in browser: {demo_path}")
        except:
            print(f"\n💡 Manually open: {demo_path}")
    
    # Start demo opener in background
    import threading
    threading.Thread(target=open_demo, daemon=True).start()
    
    try:
        # Start the Island Scorer service
        subprocess.run([venv_python, "-m", "services.island_scorer.app"], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Demo stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Error starting service: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            input("\nPress Enter to exit...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Demo stopped by user")
        sys.exit(0)
