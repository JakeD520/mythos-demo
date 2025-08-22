"""
MythOS Demo Startup Script - Week 3 Integration
Launches all three services: Island Scorer, Prose Store, and Editor
"""
import subprocess
import time
import sys
import os
import requests
from pathlib import Path


def check_port(port):
    """Check if a port is available"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def start_service(name, directory, port, command):
    """Start a service in a specific directory"""
    print(f"🚀 Starting {name} on port {port}...")
    
    # Check if already running
    if check_port(port):
        print(f"✅ {name} already running on port {port}")
        return None
    
    # Change to service directory
    service_path = Path(directory)
    if not service_path.exists():
        print(f"❌ Directory not found: {directory}")
        return None
    
    # Start the service
    try:
        process = subprocess.Popen(
            command,
            cwd=service_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if it's running
        if check_port(port):
            print(f"✅ {name} started successfully on port {port}")
            return process
        else:
            print(f"❌ {name} failed to start")
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"   stdout: {stdout.decode()[:200]}...")
                print(f"   stderr: {stderr.decode()[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start {name}: {str(e)}")
        return None


def main():
    """Main startup sequence"""
    print("🏛️ MythOS Demo - Week 3 Integration Startup")
    print("=" * 50)
    
    # Service configurations - all run from root directory for proper imports
    root_dir = Path.cwd()
    services = [
        {
            "name": "Island Scorer",
            "directory": str(root_dir),
            "port": 8000,
            "command": "D:/Dev/Mythos/mythos-dropin/.venv/Scripts/python.exe -m uvicorn services.island_scorer.app:app --host 0.0.0.0 --port 8000"
        },
        {
            "name": "Prose Store",
            "directory": str(root_dir), 
            "port": 8001,
            "command": "D:/Dev/Mythos/mythos-dropin/.venv/Scripts/python.exe -m uvicorn services.prose_store.app:app --host 0.0.0.0 --port 8001"
        },
        {
            "name": "MythOS Editor",
            "directory": str(root_dir),
            "port": 8002,
            "command": "D:/Dev/Mythos/mythos-dropin/.venv/Scripts/python.exe -m uvicorn services.editor.app:app --host 0.0.0.0 --port 8002"
        }
    ]
    
    # Start services
    processes = []
    for service in services:
        process = start_service(
            service["name"],
            service["directory"], 
            service["port"],
            service["command"]
        )
        if process:
            processes.append((service["name"], process))
        else:
            print(f"❌ Failed to start {service['name']}")
            # Clean up any started processes
            for name, p in processes:
                print(f"🛑 Stopping {name}...")
                p.terminate()
            return False
    
    print(f"\n🎉 All services started successfully!")
    
    # Wait for services to fully initialize
    print(f"⏳ Waiting for services to initialize...")
    time.sleep(5)
    
    # Final health check
    print(f"\n🏥 Final Health Check:")
    all_healthy = True
    for service in services:
        if check_port(service["port"]):
            print(f"✅ {service['name']}: http://localhost:{service['port']}")
        else:
            print(f"❌ {service['name']}: Not responding")
            all_healthy = False
    
    if all_healthy:
        print(f"\n🚀 MythOS Demo Ready!")
        print(f"📖 Open your browser to: http://localhost:8002")
        print(f"🏛️ Start writing mythological content with live worldliness feedback!")
        print(f"\n📋 Available endpoints:")
        print(f"   🏝️  Island Scorer API: http://localhost:8000/docs")
        print(f"   📚 Prose Store API: http://localhost:8001/docs")
        print(f"   ✏️  Editor Interface: http://localhost:8002")
        
        print(f"\n⌨️  Press Ctrl+C to stop all services")
        
        try:
            # Keep services running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n🛑 Shutting down services...")
            for name, process in processes:
                print(f"   Stopping {name}...")
                process.terminate()
                process.wait()
            print(f"✅ All services stopped")
    else:
        print(f"\n❌ Some services failed to start properly")
        # Clean up
        for name, process in processes:
            print(f"🛑 Stopping {name}...")
            process.terminate()
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Startup failed: {str(e)}")
        sys.exit(1)
