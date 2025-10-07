#!/usr/bin/env python3
"""
Enhanced Startup Orchestrator for Medical AI Application
Ensures proper server initialization sequence with comprehensive logging
"""

import os
import sys
import time
import subprocess
import threading
import requests
import signal
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('startup.log', mode='a')
    ]
)
logger = logging.getLogger('ORCHESTRATOR')

# Configuration
MODEL_SERVERS = {
    'qa_server': {
        'script': 'models/qa_server.py',
        'port': 5001,
        'health_endpoint': '/health',
        'timeout': 300,  # 5 minutes for model loading
        'required_status': ['ready', 'operational']
    },
    'recommendation_server': {
        'script': 'models/recommendation_server.py', 
        'port': 5002,
        'health_endpoint': '/health',
        'timeout': 300,
        'required_status': ['ready', 'operational']
    },
    'visualization_server': {
        'script': 'models/visualization_server.py',
        'port': 5003,
        'health_endpoint': '/health',
        'timeout': 300,
        'required_status': ['ready', 'operational']
    }
}

BACKEND_SERVER = {
    'command': ['node', 'server.js'],
    'cwd': 'backend',
    'port': 3001,
    'health_endpoint': '/health',
    'timeout': 60
}

FRONTEND_SERVER = {
    'command': ['npm', 'run', 'dev'],
    'cwd': '.',
    'port': 5173,
    'timeout': 30
}

class EnhancedStartupOrchestrator:
    def __init__(self):
        self.processes = {}
        self.running = True
        self.startup_logs = []
        self.performance_metrics = {}
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Enhanced Startup Orchestrator initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals with proper cleanup"""
        logger.info(f"Shutdown signal {signum} received, stopping all services...")
        self.running = False
        self._stop_all_processes()
        self._generate_shutdown_report()
        sys.exit(0)
    
    def _log_event(self, event: str, details: Dict = None):
        """Log events with timestamps for later analysis"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'event': event,
            'details': details or {}
        }
        self.startup_logs.append(log_entry)
        logger.info(f"Event: {event}", extra={'details': details})
    
    def _check_prerequisites(self) -> bool:
        """Enhanced prerequisite checking with detailed logging"""
        logger.info("Starting comprehensive prerequisites check...")
        self._log_event("prerequisites_check_started")
        
        checks = [
            self._check_python,
            self._check_nodejs,
            self._check_npm,
            self._check_data_files,
            self._check_dependencies,
            self._check_ports
        ]
        
        for check in checks:
            try:
                if not check():
                    self._log_event("prerequisites_check_failed", {'check': check.__name__})
                    return False
            except Exception as e:
                logger.error(f"Prerequisites check {check.__name__} failed: {e}")
                return False
        
        self._log_event("prerequisites_check_completed")
        logger.info("✅ All prerequisites checks passed")
        return True
    
    def _check_python(self) -> bool:
        """Check Python availability"""
        logger.info("Checking Python availability...")
        
        for python_cmd in ['python', 'python3']:
            try:
                result = subprocess.run([python_cmd, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    logger.info(f"✅ {python_cmd} available: {version}")
                    self._log_event("python_check_passed", {'command': python_cmd, 'version': version})
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        logger.error("❌ Python not found")
        return False
    
    def _check_nodejs(self) -> bool:
        """Check Node.js availability"""
        logger.info("Checking Node.js availability...")
        
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✅ Node.js available: {version}")
                self._log_event("nodejs_check_passed", {'version': version})
                return True
        except Exception as e:
            logger.error(f"❌ Node.js check failed: {e}")
        
        return False
    
    def _check_npm(self) -> bool:
        """Check npm availability"""
        logger.info("Checking npm availability...")
        
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✅ npm available: {version}")
                self._log_event("npm_check_passed", {'version': version})
                return True
        except Exception as e:
            logger.error(f"❌ npm check failed: {e}")
        
        return False
    
    def _check_data_files(self) -> bool:
        """Check for required data files"""
        logger.info("Checking data files...")
        
        required_files = [
            Path("data/medquad_processed.csv"),
            Path("data/drugs_side_effects.csv"),
            Path("embeddings/encoded_docs.npy"),
            Path("embeddings/faiss_index_cpu.index")
        ]
        
        missing_files = []
        for file_path in required_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
                logger.warning(f"⚠️  Missing: {file_path}")
            else:
                logger.info(f"✅ Found: {file_path}")
        
        if missing_files:
            logger.warning(f"Missing {len(missing_files)} data files - models will use fallback data")
            self._log_event("data_files_check_warning", {'missing_files': missing_files})
        else:
            self._log_event("data_files_check_passed")
        
        return True  # Non-blocking, just warnings
    
    def _check_dependencies(self) -> bool:
        """Check and install dependencies if needed"""
        logger.info("Checking dependencies...")
        
        # Check backend dependencies
        backend_node_modules = Path("backend/node_modules")
        if not backend_node_modules.exists():
            logger.info("Installing backend dependencies...")
            try:
                result = subprocess.run(['npm', 'install'], cwd='backend', 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    logger.error(f"Backend dependency installation failed: {result.stderr}")
                    return False
                logger.info("✅ Backend dependencies installed")
                self._log_event("backend_deps_installed")
            except Exception as e:
                logger.error(f"Error installing backend dependencies: {e}")
                return False
        
        # Check frontend dependencies
        frontend_node_modules = Path("node_modules")
        if not frontend_node_modules.exists():
            logger.info("Installing frontend dependencies...")
            try:
                result = subprocess.run(['npm', 'install'], 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    logger.error(f"Frontend dependency installation failed: {result.stderr}")
                    return False
                logger.info("✅ Frontend dependencies installed")
                self._log_event("frontend_deps_installed")
            except Exception as e:
                logger.error(f"Error installing frontend dependencies: {e}")
                return False
        
        # Check Python dependencies
        try:
            import flask, flask_cors, requests, numpy, faiss
            logger.info("✅ Python dependencies available")
            self._log_event("python_deps_check_passed")
        except ImportError as e:
            logger.warning(f"⚠️  Some Python dependencies missing: {e}")
            logger.warning("Run: pip install -r requirements.txt")
            self._log_event("python_deps_check_warning", {'missing': str(e)})
        
        return True
    
    def _check_ports(self) -> bool:
        """Check if required ports are available"""
        logger.info("Checking port availability...")
        
        ports_to_check = [3001, 5001, 5002, 5003, 5173]
        occupied_ports = []
        
        for port in ports_to_check:
            if self._is_port_occupied(port):
                occupied_ports.append(port)
                logger.warning(f"⚠️  Port {port} is already occupied")
            else:
                logger.info(f"✅ Port {port} is available")
        
        if occupied_ports:
            logger.warning(f"Some ports are occupied: {occupied_ports}")
            logger.warning("This may cause conflicts during startup")
            self._log_event("ports_check_warning", {'occupied_ports': occupied_ports})
        else:
            self._log_event("ports_check_passed")
        
        return True  # Non-blocking
    
    def _is_port_occupied(self, port: int) -> bool:
        """Check if a port is occupied"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except socket.error:
                return True
    
    def _start_model_server(self, name: str, config: Dict) -> bool:
        """Start a model server with enhanced monitoring"""
        logger.info(f"Starting {name}...")
        start_time = time.time()
        self._log_event(f"{name}_start_initiated")
        
        try:
            # Determine Python command
            python_cmd = self._get_python_command()
            if not python_cmd:
                logger.error(f"No Python interpreter found for {name}")
                return False
            
            # Set environment variables
            env = os.environ.copy()
            env[f'{name.upper()}_PORT'] = str(config['port'])
            env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
            
            # Start process
            process = subprocess.Popen(
                [python_cmd, config['script']],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[name] = process
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_process_output, 
                args=(name, process),
                daemon=True
            )
            monitor_thread.start()
            
            startup_time = time.time() - start_time
            self.performance_metrics[f"{name}_startup_time"] = startup_time
            self._log_event(f"{name}_started", {'startup_time': startup_time})
            
            logger.info(f"✅ {name} process started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            self._log_event(f"{name}_start_failed", {'error': str(e)})
            return False
    
    def _get_python_command(self) -> Optional[str]:
        """Get available Python command"""
        for cmd in ['python', 'python3']:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, check=True)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return None
    
    def _monitor_process_output(self, name: str, process: subprocess.Popen):
        """Monitor process output with enhanced logging"""
        process_logger = logging.getLogger(name.upper())
        
        try:
            while self.running and process.poll() is None:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    process_logger.info(line)
                    
                    # Track important events
                    if "error" in line.lower() or "exception" in line.lower():
                        self._log_event(f"{name}_error_detected", {'message': line})
                    elif "ready" in line.lower() or "initialized" in line.lower():
                        self._log_event(f"{name}_ready_signal", {'message': line})
        except Exception as e:
            process_logger.error(f"Output monitoring failed: {e}")
    
    def _wait_for_server_ready(self, name: str, port: int, health_endpoint: str, timeout: int = 180) -> bool:
        """Wait for server readiness with detailed progress logging"""
        logger.info(f"Waiting for {name} to be ready on port {port} (timeout: {timeout}s)...")
        
        start_time = time.time()
        attempt = 0
        last_status = None
        
        while time.time() - start_time < timeout:
            if not self.running:
                return False
            
            attempt += 1
            try:
                response = requests.get(
                    f"http://localhost:{port}{health_endpoint}", 
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    
                    if status != last_status:
                        logger.info(f"{name} status: {status}")
                        last_status = status
                        self._log_event(f"{name}_status_update", {
                            'status': status, 
                            'attempt': attempt,
                            'elapsed': time.time() - start_time
                        })
                    
                    if status in ['ready', 'operational', 'OK']:
                        ready_time = time.time() - start_time
                        self.performance_metrics[f"{name}_ready_time"] = ready_time
                        logger.info(f"✅ {name} is ready! (took {ready_time:.1f}s)")
                        self._log_event(f"{name}_ready", {
                            'ready_time': ready_time,
                            'attempts': attempt
                        })
                        return True
                        
            except requests.exceptions.RequestException as e:
                if attempt % 10 == 0:  # Log every 10th attempt to reduce noise
                    logger.info(f"{name} not ready yet (attempt {attempt}): {type(e).__name__}")
            
            time.sleep(3)  # Check every 3 seconds
        
        elapsed = time.time() - start_time
        logger.error(f"❌ {name} failed to become ready within {timeout}s (elapsed: {elapsed:.1f}s)")
        self._log_event(f"{name}_ready_timeout", {
            'timeout': timeout,
            'elapsed': elapsed,
            'attempts': attempt
        })
        return False
    
    def _start_backend_server(self) -> bool:
        """Start backend server with enhanced monitoring"""
        logger.info("Starting backend API gateway...")
        start_time = time.time()
        self._log_event("backend_start_initiated")
        
        try:
            # Verify backend directory and files
            if not Path('backend/server.js').exists():
                logger.error("Backend server.js not found")
                return False
            
            # Set environment variables
            env = os.environ.copy()
            env.update({
                'QA_SERVER_URL': 'http://localhost:5001',
                'REC_SERVER_URL': 'http://localhost:5002',
                'VIZ_SERVER_URL': 'http://localhost:5003',
                'NODE_ENV': 'production',
                'PORT': '3001'
            })
            
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
            monitor_thread = threading.Thread(
                target=self._monitor_process_output,
                args=('backend', process),
                daemon=True
            )
            monitor_thread.start()
            
            startup_time = time.time() - start_time
            self.performance_metrics['backend_startup_time'] = startup_time
            self._log_event("backend_started", {'startup_time': startup_time})
            
            logger.info(f"✅ Backend server started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start backend server: {e}")
            self._log_event("backend_start_failed", {'error': str(e)})
            return False
    
    def _start_frontend_server(self) -> bool:
        """Start frontend server with monitoring"""
        logger.info("Starting frontend development server...")
        start_time = time.time()
        self._log_event("frontend_start_initiated")
        
        try:
            # Verify frontend files
            if not Path('package.json').exists():
                logger.error("Frontend package.json not found")
                return False
            
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
            monitor_thread = threading.Thread(
                target=self._monitor_process_output,
                args=('frontend', process),
                daemon=True
            )
            monitor_thread.start()
            
            startup_time = time.time() - start_time
            self.performance_metrics['frontend_startup_time'] = startup_time
            self._log_event("frontend_started", {'startup_time': startup_time})
            
            logger.info(f"✅ Frontend server started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start frontend server: {e}")
            self._log_event("frontend_start_failed", {'error': str(e)})
            return False
    
    def _stop_all_processes(self):
        """Stop all processes with proper cleanup"""
        logger.info("Stopping all processes...")
        self._log_event("shutdown_initiated")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"Stopping {name} (PID: {process.pid})...")
                try:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                        logger.info(f"✅ {name} stopped gracefully")
                        self._log_event(f"{name}_stopped_gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {name}...")
                        process.kill()
                        process.wait()
                        self._log_event(f"{name}_force_killed")
                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")
                    self._log_event(f"{name}_stop_error", {'error': str(e)})
    
    def _generate_startup_report(self):
        """Generate startup performance report"""
        print("\n" + "="*80)
        print("📊 STARTUP PERFORMANCE REPORT")
        print("="*80)
        
        for metric, value in self.performance_metrics.items():
            print(f"⏱️  {metric}: {value:.2f}s")
        
        print(f"\n📝 Total Events Logged: {len(self.startup_logs)}")
        print("="*80)
    
    def _generate_shutdown_report(self):
        """Generate shutdown report"""
        logger.info("Generating shutdown report...")
        
        # Save logs to file
        with open('startup_logs.json', 'w') as f:
            json.dump({
                'startup_logs': self.startup_logs,
                'performance_metrics': self.performance_metrics,
                'shutdown_time': datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info("Shutdown report saved to startup_logs.json")
    
    def start_application(self) -> bool:
        """Start the complete application stack with comprehensive monitoring"""
        print("\n" + "="*80)
        print("🩺 ENHANCED MEDICAL AI APPLICATION STARTUP ORCHESTRATOR")
        print("="*80)
        
        total_start_time = time.time()
        self._log_event("application_startup_initiated")
        
        try:
            # Phase 1: Prerequisites
            logger.info("\n🔍 PHASE 1: Prerequisites Check")
            print("-" * 50)
            if not self._check_prerequisites():
                logger.error("Prerequisites check failed. Exiting.")
                return False
            
            # Phase 2: Model Servers
            logger.info("\n🤖 PHASE 2: Starting AI Model Servers")
            print("-" * 50)
            
            for name, config in MODEL_SERVERS.items():
                if not self._start_model_server(name, config):
                    logger.error(f"Failed to start {name}")
                    return False
                time.sleep(5)  # Stagger startup
            
            # Phase 3: Wait for Model Readiness
            logger.info("\n⏳ PHASE 3: Waiting for AI Models to Initialize")
            print("-" * 50)
            
            for name, config in MODEL_SERVERS.items():
                if not self._wait_for_server_ready(
                    name, config['port'], config['health_endpoint'], config['timeout']
                ):
                    logger.error(f"{name} failed to become ready")
                    return False
            
            logger.info("\n✅ All AI model servers are operational!")
            
            # Phase 4: Backend Server
            logger.info("\n🔧 PHASE 4: Starting Backend API Gateway")
            print("-" * 50)
            
            if not self._start_backend_server():
                logger.error("Failed to start backend server")
                return False
            
            time.sleep(10)
            
            if not self._wait_for_server_ready(
                'backend', BACKEND_SERVER['port'], 
                BACKEND_SERVER['health_endpoint'], BACKEND_SERVER['timeout']
            ):
                logger.error("Backend server failed to start")
                return False
            
            # Phase 5: Frontend Server
            logger.info("\n🌐 PHASE 5: Starting Frontend Web Server")
            print("-" * 50)
            
            if not self._start_frontend_server():
                logger.error("Failed to start frontend server")
                return False
            
            time.sleep(15)  # Give frontend time to compile
            
            # Application Ready!
            total_time = time.time() - total_start_time
            self.performance_metrics['total_startup_time'] = total_time
            self._log_event("application_startup_completed", {'total_time': total_time})
            
            print("\n" + "="*80)
            print("🚀 MEDICAL AI APPLICATION IS NOW RUNNING!")
            print("="*80)
            print(f"🌐 Frontend: http://localhost:{FRONTEND_SERVER['port']}")
            print(f"🔧 Backend API: http://localhost:{BACKEND_SERVER['port']}")
            print(f"📊 Health Check: http://localhost:{BACKEND_SERVER['port']}/health")
            print(f"📚 API Docs: http://localhost:{BACKEND_SERVER['port']}/api")
            print("\n🤖 AI Model Servers:")
            for name, config in MODEL_SERVERS.items():
                print(f"   • {name}: http://localhost:{config['port']}")
            print("="*80)
            print(f"\n⚡ Total startup time: {total_time:.1f} seconds")
            print("\n✨ Open http://localhost:5173 in your browser")
            print("\n🛑 Press Ctrl+C to stop all services")
            print("="*80)
            
            self._generate_startup_report()
            
            # Monitor running processes
            logger.info("\n👁️  Monitoring running processes...")
            try:
                while self.running:
                    time.sleep(5)
                    
                    # Check process health
                    for name, process in self.processes.items():
                        if process.poll() is not None:
                            logger.error(f"⚠️  {name} process has stopped unexpectedly")
                            self._log_event(f"{name}_unexpected_stop")
                            
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            self._log_event("application_startup_failed", {'error': str(e)})
            return False
            
        finally:
            self._stop_all_processes()
            self._generate_shutdown_report()

def main():
    """Main entry point"""
    orchestrator = EnhancedStartupOrchestrator()
    success = orchestrator.start_application()
    
    if not success:
        print("\n❌ APPLICATION STARTUP FAILED")
        print("\n🔧 Quick Fix Steps:")
        print("1. Check startup.log for detailed error information")
        print("2. Install backend dependencies: cd backend && npm install")
        print("3. Install frontend dependencies: npm install")
        print("4. Install Python dependencies: pip install -r requirements.txt")
        print("5. Ensure all required data files are present")
        print("6. Check that no other services are using required ports")
        print("7. Try running again: python startup_orchestrator.py")
        sys.exit(1)
    else:
        print("\n✅ Application shutdown complete")
        print("📊 Check startup_logs.json for detailed performance metrics")

if __name__ == "__main__":
    main()