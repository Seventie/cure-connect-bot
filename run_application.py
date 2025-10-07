#!/usr/bin/env python3
"""
Comprehensive Application Runner for Medical AI Web Application
Ensures proper sequential startup with model readiness checks
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
from typing import Dict, List, Optional

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('application.log', mode='a')
    ]
)
logger = logging.getLogger('APP_RUNNER')

class ApplicationRunner:
    def __init__(self):
        self.processes = {}
        self.running = True
        self.startup_events = []
        
        # Model servers configuration
        self.model_servers = {
            'qa_server': {'port': 5001, 'script': 'models/qa_server.py', 'timeout': 180},
            'recommendation_server': {'port': 5002, 'script': 'models/recommendation_server.py', 'timeout': 120},
            'visualization_server': {'port': 5003, 'script': 'models/visualization_server.py', 'timeout': 120}
        }
        
        # Backend and frontend configuration  
        self.backend_config = {'port': 3001, 'cwd': 'backend', 'cmd': ['node', 'server.js']}
        self.frontend_config = {'port': 5173, 'cwd': '.', 'cmd': ['npm', 'run', 'dev']}
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Application Runner initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Shutdown signal {signum} received, stopping all services...")
        self.running = False
        self._stop_all_processes()
        sys.exit(0)
    
    def _log_event(self, event: str, details: Dict = None):
        """Log events with timestamps"""
        timestamp = datetime.now().isoformat()
        self.startup_events.append({
            'timestamp': timestamp,
            'event': event,
            'details': details or {}
        })
        logger.info(f"Event: {event}", extra={'details': details})
    
    def _check_prerequisites(self) -> bool:
        """Check all prerequisites"""
        logger.info("Checking prerequisites...")
        
        # Check Python
        try:
            result = subprocess.run(['python', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Python available: {result.stdout.strip()}")
            else:
                logger.error("❌ Python not found")
                return False
        except FileNotFoundError:
            logger.error("❌ Python not found")
            return False
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Node.js available: {result.stdout.strip()}")
            else:
                logger.error("❌ Node.js not found")
                return False
        except FileNotFoundError:
            logger.error("❌ Node.js not found")
            return False
        
        # Check required files
        required_files = [
            'models/qa_server.py',
            'models/recommendation_server.py', 
            'models/visualization_server.py',
            'backend/server.js',
            'package.json'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                logger.error(f"❌ Required file missing: {file_path}")
                return False
            logger.info(f"✅ Found: {file_path}")
        
        # Check data files (warnings only)
        data_files = [
            'data/medquad_processed.csv',
            'data/drugs_side_effects.csv',
            'embeddings/encoded_docs.npy'
        ]
        
        for file_path in data_files:
            if not Path(file_path).exists():
                logger.warning(f"⚠️  Missing data file: {file_path} (will use fallback)")
            else:
                logger.info(f"✅ Found data: {file_path}")
        
        return True
    
    def _start_model_server(self, name: str, config: Dict) -> bool:
        """Start a model server"""
        logger.info(f"Starting {name}...")
        
        try:
            env = os.environ.copy()
            env[f'{name.upper()}_PORT'] = str(config['port'])
            env['PYTHONUNBUFFERED'] = '1'
            
            process = subprocess.Popen(
                ['python', config['script']],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[name] = process
            
            # Start output monitoring
            monitor_thread = threading.Thread(
                target=self._monitor_output,
                args=(name, process),
                daemon=True
            )
            monitor_thread.start()
            
            logger.info(f"✅ {name} process started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            return False
    
    def _monitor_output(self, name: str, process: subprocess.Popen):
        """Monitor process output"""
        process_logger = logging.getLogger(name.upper())
        
        try:
            while self.running and process.poll() is None:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    if line:  # Only log non-empty lines
                        process_logger.info(line)
        except Exception as e:
            process_logger.error(f"Output monitoring failed: {e}")
    
    def _wait_for_server_ready(self, name: str, port: int, timeout: int = 120) -> bool:
        """Wait for server to be ready"""
        logger.info(f"Waiting for {name} to be ready on port {port}...")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            if not self.running:
                return False
            
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    
                    if status != last_status:
                        logger.info(f"{name} status: {status}")
                        last_status = status
                    
                    if status in ['ready', 'operational', 'OK']:
                        ready_time = time.time() - start_time
                        logger.info(f"✅ {name} is ready! (took {ready_time:.1f}s)")
                        return True
                        
            except requests.exceptions.RequestException:
                pass  # Continue waiting
            
            time.sleep(2)
        
        logger.error(f"❌ {name} failed to become ready within {timeout}s")
        return False
    
    def _start_backend_server(self) -> bool:
        """Start backend server"""
        logger.info("Starting backend API gateway...")
        
        try:
            env = os.environ.copy()
            env.update({
                'QA_SERVER_URL': 'http://localhost:5001',
                'REC_SERVER_URL': 'http://localhost:5002',
                'VIZ_SERVER_URL': 'http://localhost:5003',
                'NODE_ENV': 'production',
                'PORT': '3001'
            })
            
            process = subprocess.Popen(
                self.backend_config['cmd'],
                cwd=self.backend_config['cwd'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes['backend'] = process
            
            # Monitor backend output
            monitor_thread = threading.Thread(
                target=self._monitor_output,
                args=('backend', process),
                daemon=True
            )
            monitor_thread.start()
            
            logger.info(f"✅ Backend server started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start backend server: {e}")
            return False
    
    def _start_frontend_server(self) -> bool:
        """Start frontend server"""
        logger.info("Starting frontend development server...")
        
        try:
            process = subprocess.Popen(
                self.frontend_config['cmd'],
                cwd=self.frontend_config['cwd'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes['frontend'] = process
            
            # Monitor frontend output
            monitor_thread = threading.Thread(
                target=self._monitor_output,
                args=('frontend', process),
                daemon=True
            )
            monitor_thread.start()
            
            logger.info(f"✅ Frontend server started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start frontend server: {e}")
            return False
    
    def _stop_all_processes(self):
        """Stop all processes"""
        logger.info("Stopping all processes...")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"Stopping {name}...")
                try:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                        logger.info(f"✅ {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {name}...")
                        process.kill()
                        process.wait()
                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")
    
    def run_application(self) -> bool:
        """Run the complete application"""
        print("\n" + "="*80)
        print("🩺 MEDICAL AI APPLICATION RUNNER")
        print("="*80)
        
        try:
            # Phase 1: Prerequisites
            logger.info("\n🔍 PHASE 1: Prerequisites Check")
            if not self._check_prerequisites():
                logger.error("Prerequisites check failed")
                return False
            
            # Phase 2: Start Model Servers
            logger.info("\n🤖 PHASE 2: Starting AI Model Servers")
            for name, config in self.model_servers.items():
                if not self._start_model_server(name, config):
                    logger.error(f"Failed to start {name}")
                    return False
                time.sleep(3)  # Stagger startup
            
            # Phase 3: Wait for Models to be Ready
            logger.info("\n⏳ PHASE 3: Waiting for AI Models to Initialize")
            for name, config in self.model_servers.items():
                if not self._wait_for_server_ready(name, config['port'], config['timeout']):
                    logger.error(f"{name} failed to become ready")
                    return False
            
            logger.info("\n✅ All AI model servers are operational!")
            
            # Phase 4: Start Backend
            logger.info("\n🔧 PHASE 4: Starting Backend API Gateway")
            if not self._start_backend_server():
                logger.error("Failed to start backend server")
                return False
            
            time.sleep(5)
            if not self._wait_for_server_ready('backend', 3001, 60):
                logger.error("Backend server failed to start")
                return False
            
            # Phase 5: Start Frontend
            logger.info("\n🌐 PHASE 5: Starting Frontend Web Server")
            if not self._start_frontend_server():
                logger.error("Failed to start frontend server")
                return False
            
            time.sleep(10)  # Give frontend time to compile
            
            # Application Ready
            print("\n" + "="*80)
            print("🚀 MEDICAL AI APPLICATION IS NOW RUNNING!")
            print("="*80)
            print(f"🌐 Frontend: http://localhost:5173")
            print(f"🔧 Backend API: http://localhost:3001")
            print(f"📊 Health Check: http://localhost:3001/health")
            print(f"📚 API Docs: http://localhost:3001/api")
            print("\n🤖 AI Model Servers:")
            for name, config in self.model_servers.items():
                print(f"   • {name}: http://localhost:{config['port']}")
            print("="*80)
            print("\n✨ Open http://localhost:5173 in your browser")
            print("\n🛑 Press Ctrl+C to stop all services")
            print("="*80)
            
            # Monitor processes
            logger.info("\n👁️  Monitoring processes...")
            while self.running:
                time.sleep(5)
                
                # Check if any process has stopped
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        logger.error(f"⚠️  {name} process has stopped unexpectedly")
                        return False
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            return True
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            return False
        finally:
            self._stop_all_processes()

def main():
    """Main entry point"""
    runner = ApplicationRunner()
    success = runner.run_application()
    
    if not success:
        print("\n❌ APPLICATION STARTUP FAILED")
        print("\n🔧 Check application.log for detailed error information")
        sys.exit(1)
    else:
        print("\n✅ Application shutdown complete")

if __name__ == "__main__":
    main()