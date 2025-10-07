#!/usr/bin/env python3
"""
Startup Orchestrator for Medical AI Application
Ensures models are loaded before starting the web server
"""

import os
import sys
import time
import subprocess
import threading
import requests
import signal
from pathlib import Path

# Configuration
MODEL_SERVERS = {
    'qa_server': {
        'script': 'models/qa_server.py',
        'port': 5001,
        'health_endpoint': '/health'
    },
    'recommendation_server': {
        'script': 'models/recommendation_server.py', 
        'port': 5002,
        'health_endpoint': '/health'
    },
    'visualization_server': {
        'script': 'models/visualization_server.py',
        'port': 5003,
        'health_endpoint': '/health'
    }
}

BACKEND_SERVER = {
    'command': ['npm', 'start'],
    'cwd': 'backend',
    'port': 3001,
    'health_endpoint': '/health'
}

FRONTEND_SERVER = {
    'command': ['npm', 'run', 'dev'],
    'cwd': '.',
    'port': 5173
}

class StartupOrchestrator:
    def __init__(self):
        self.processes = {}
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n[ORCHESTRATOR] Shutdown signal received, stopping all services...")
        self.running = False
        self._stop_all_processes()
        sys.exit(0)
    
    def _check_prerequisites(self):
        """Check if all required files and dependencies exist"""
        print("[ORCHESTRATOR] Checking prerequisites...")
        
        # Check if data files exist
        required_data_files = [
            Path("data/medquad_processed.csv"),
            Path("data/drugs_side_effects.csv")
        ]
        
        missing_files = []
        for file_path in required_data_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        if missing_files:
            print(f"[ORCHESTRATOR] Warning: Missing data files: {missing_files}")
            print("[ORCHESTRATOR] Models will use fallback data")
        
        # Check if Python is available
        try:
            result = subprocess.run(['python', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[ORCHESTRATOR] Python available: {result.stdout.strip()}")
            else:
                # Try python3
                result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[ORCHESTRATOR] Python3 available: {result.stdout.strip()}")
                else:
                    raise Exception("Python not found")
        except Exception as e:
            print(f"[ORCHESTRATOR] Error: Python not available - {e}")
            return False
        
        # Check if Node.js is available
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[ORCHESTRATOR] Node.js available: {result.stdout.strip()}")
            else:
                raise Exception("Node.js not found")
        except Exception as e:
            print(f"[ORCHESTRATOR] Error: Node.js not available - {e}")
            return False
        
        # Check if npm is available
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[ORCHESTRATOR] npm available: {result.stdout.strip()}")
            else:
                raise Exception("npm not found")
        except Exception as e:
            print(f"[ORCHESTRATOR] Error: npm not available - {e}")
            return False
        
        # Check if backend dependencies are installed
        backend_node_modules = Path("backend/node_modules")
        if not backend_node_modules.exists():
            print("[ORCHESTRATOR] Warning: Backend dependencies not installed")
            print("[ORCHESTRATOR] Installing backend dependencies...")
            try:
                result = subprocess.run(['npm', 'install'], cwd='backend', capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"[ORCHESTRATOR] Error installing backend dependencies: {result.stderr}")
                    return False
                print("[ORCHESTRATOR] Backend dependencies installed successfully")
            except Exception as e:
                print(f"[ORCHESTRATOR] Error: Could not install backend dependencies - {e}")
                return False
        
        # Check if frontend dependencies are installed
        frontend_node_modules = Path("node_modules")
        if not frontend_node_modules.exists():
            print("[ORCHESTRATOR] Warning: Frontend dependencies not installed")
            print("[ORCHESTRATOR] Installing frontend dependencies...")
            try:
                result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"[ORCHESTRATOR] Error installing frontend dependencies: {result.stderr}")
                    return False
                print("[ORCHESTRATOR] Frontend dependencies installed successfully")
            except Exception as e:
                print(f"[ORCHESTRATOR] Error: Could not install frontend dependencies - {e}")
                return False
        
        # Check if Flask is available
        try:
            result = subprocess.run(['python', '-c', 'import flask; print(flask.__version__)'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[ORCHESTRATOR] Flask available: {result.stdout.strip()}")
            else:
                # Try with python3
                result = subprocess.run(['python3', '-c', 'import flask; print(flask.__version__)'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[ORCHESTRATOR] Flask available: {result.stdout.strip()}")
                else:
                    print("[ORCHESTRATOR] Warning: Flask not available. Run: pip install flask flask-cors")
        except Exception as e:
            print(f"[ORCHESTRATOR] Warning: Could not check Flask: {e}")
        
        print("[ORCHESTRATOR] Prerequisites check completed")
        return True
    
    def _start_model_server(self, name, config):
        """Start a model server process"""
        print(f"[ORCHESTRATOR] Starting {name}...")
        
        try:
            # Set environment variables
            env = os.environ.copy()
            env[f'{name.upper()}_PORT'] = str(config['port'])
            
            # Try python first, then python3
            python_cmd = 'python'
            try:
                subprocess.run(['python', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                python_cmd = 'python3'
            
            process = subprocess.Popen(
                [python_cmd, config['script']],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[name] = process
            
            # Start thread to monitor output
            def monitor_output():
                while self.running and process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        print(f"[{name.upper()}] {line.strip()}")
            
            threading.Thread(target=monitor_output, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Failed to start {name}: {e}")
            return False
    
    def _wait_for_server_ready(self, name, port, health_endpoint, timeout=180):
        """Wait for a server to become ready"""
        print(f"[ORCHESTRATOR] Waiting for {name} to be ready on port {port}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.running:
                return False
                
            try:
                response = requests.get(f"http://localhost:{port}{health_endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    if status in ['ready', 'operational', 'OK']:
                        print(f"[ORCHESTRATOR] ✅ {name} is ready!")
                        return True
                    elif status == 'initializing':
                        print(f"[ORCHESTRATOR] {name} is still initializing...")
                    else:
                        print(f"[ORCHESTRATOR] {name} status: {status}")
            except requests.exceptions.RequestException as e:
                print(f"[ORCHESTRATOR] {name} not ready yet: {e}")
            
            time.sleep(5)
        
        print(f"[ORCHESTRATOR] ❌ {name} failed to become ready within {timeout}s")
        return False
    
    def _start_backend_server(self):
        """Start the backend server"""
        print("[ORCHESTRATOR] Starting backend server...")
        
        try:
            # Set environment variables for backend
            env = os.environ.copy()
            env['QA_SERVER_URL'] = 'http://localhost:5001'
            env['REC_SERVER_URL'] = 'http://localhost:5002' 
            env['VIZ_SERVER_URL'] = 'http://localhost:5003'
            
            # Check if package.json exists
            package_json = Path(BACKEND_SERVER['cwd']) / 'package.json'
            if not package_json.exists():
                raise Exception(f"Backend package.json not found at {package_json}")
            
            # Check if node_modules exists
            node_modules = Path(BACKEND_SERVER['cwd']) / 'node_modules'
            if not node_modules.exists():
                raise Exception(f"Backend dependencies not installed. Run: cd {BACKEND_SERVER['cwd']} && npm install")
            
            process = subprocess.Popen(
                BACKEND_SERVER['command'],
                cwd=BACKEND_SERVER['cwd'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes['backend'] = process
            
            # Monitor backend output
            def monitor_backend():
                while self.running and process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        print(f"[BACKEND] {line.strip()}")
            
            threading.Thread(target=monitor_backend, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Failed to start backend server: {e}")
            return False
    
    def _start_frontend_server(self):
        """Start the frontend server"""
        print("[ORCHESTRATOR] Starting frontend server...")
        
        try:
            # Check if package.json exists
            package_json = Path('package.json')
            if not package_json.exists():
                raise Exception("Frontend package.json not found")
            
            # Check if node_modules exists
            node_modules = Path('node_modules')
            if not node_modules.exists():
                raise Exception("Frontend dependencies not installed. Run: npm install")
            
            process = subprocess.Popen(
                FRONTEND_SERVER['command'],
                cwd=FRONTEND_SERVER['cwd'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes['frontend'] = process
            
            # Monitor frontend output
            def monitor_frontend():
                while self.running and process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        print(f"[FRONTEND] {line.strip()}")
            
            threading.Thread(target=monitor_frontend, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Failed to start frontend server: {e}")
            return False
    
    def _stop_all_processes(self):
        """Stop all running processes"""
        print("[ORCHESTRATOR] Stopping all processes...")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"[ORCHESTRATOR] Stopping {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"[ORCHESTRATOR] Force killing {name}...")
                    process.kill()
                except Exception as e:
                    print(f"[ORCHESTRATOR] Error stopping {name}: {e}")
    
    def start_application(self):
        """Start the complete application stack"""
        print("\n" + "="*80)
        print("🩺 MEDICAL AI APPLICATION STARTUP ORCHESTRATOR")
        print("="*80)
        
        try:
            # Step 1: Check prerequisites
            if not self._check_prerequisites():
                print("[ORCHESTRATOR] Prerequisites check failed. Exiting.")
                return False
            
            # Step 2: Start model servers
            print("\n[ORCHESTRATOR] Phase 1: Starting AI Model Servers...")
            print("-" * 50)
            
            model_servers_started = True
            for name, config in MODEL_SERVERS.items():
                if not self._start_model_server(name, config):
                    model_servers_started = False
                    break
                
                # Give the server a moment to start
                time.sleep(5)
            
            if not model_servers_started:
                print("[ORCHESTRATOR] Failed to start model servers")
                return False
            
            # Step 3: Wait for all model servers to be ready
            print("\n[ORCHESTRATOR] Phase 2: Waiting for AI Models to Initialize...")
            print("-" * 50)
            
            all_models_ready = True
            for name, config in MODEL_SERVERS.items():
                if not self._wait_for_server_ready(name, config['port'], config['health_endpoint']):
                    all_models_ready = False
                    break
            
            if not all_models_ready:
                print("[ORCHESTRATOR] Model servers failed to become ready")
                return False
            
            print("\n✅ All AI model servers are operational!")
            
            # Step 4: Start backend server
            print("\n[ORCHESTRATOR] Phase 3: Starting Backend API Server...")
            print("-" * 50)
            
            if not self._start_backend_server():
                return False
            
            time.sleep(10)  # Give backend time to start
            
            if not self._wait_for_server_ready('backend', BACKEND_SERVER['port'], BACKEND_SERVER['health_endpoint'], timeout=60):
                print("[ORCHESTRATOR] Backend server failed to start")
                return False
            
            # Step 5: Start frontend server
            print("\n[ORCHESTRATOR] Phase 4: Starting Frontend Web Server...")
            print("-" * 50)
            
            if not self._start_frontend_server():
                return False
            
            # Wait a bit for frontend to start
            time.sleep(15)
            
            # Step 6: Application is ready!
            print("\n" + "="*80)
            print("🚀 MEDICAL AI APPLICATION IS NOW RUNNING!")
            print("="*80)
            print(f"🌐 Frontend: http://localhost:{FRONTEND_SERVER['port']}")
            print(f"🔧 Backend API: http://localhost:{BACKEND_SERVER['port']}")
            print(f"🤖 QA Model: http://localhost:{MODEL_SERVERS['qa_server']['port']}")
            print(f"💊 Recommendation Model: http://localhost:{MODEL_SERVERS['recommendation_server']['port']}")
            print(f"📊 Visualization Model: http://localhost:{MODEL_SERVERS['visualization_server']['port']}")
            print("="*80)
            print("\n✨ Open http://localhost:5173 in your browser to access the application")
            print("\n🛑 Press Ctrl+C to stop all services")
            print("="*80)
            
            # Keep running until interrupted
            try:
                while self.running:
                    time.sleep(1)
                    
                    # Check if any process has died
                    for name, process in self.processes.items():
                        if process.poll() is not None:
                            print(f"[ORCHESTRATOR] Warning: {name} process has stopped")
            
            except KeyboardInterrupt:
                pass
            
            return True
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Error during startup: {e}")
            return False
            
        finally:
            self._stop_all_processes()

def main():
    orchestrator = StartupOrchestrator()
    success = orchestrator.start_application()
    
    if not success:
        print("[ORCHESTRATOR] Application startup failed")
        print("\n🔧 Quick Fix Steps:")
        print("1. Install backend dependencies: cd backend && npm install")
        print("2. Install frontend dependencies: npm install")
        print("3. Install Python dependencies: pip install -r requirements.txt")
        print("4. Try running again: python startup_orchestrator.py")
        sys.exit(1)
    else:
        print("[ORCHESTRATOR] Application shutdown complete")

if __name__ == "__main__":
    main()