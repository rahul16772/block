#!/usr/bin/env python3
"""
Standalone HTTP server runner for BlockAssist.
This script runs the Next.js authentication server independently from the main BlockAssist process.
Designed to improve WSL compatibility by separating concerns.
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from subprocess import Popen
from typing import Optional

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

class HTTPServerManager:
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.yarn_process: Optional[Popen] = None
        self.running = False
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)
        
    def setup_environment(self):
        """Set up the environment for the HTTP server."""
        logger.info("Setting up HTTP server environment")
        
        # Test if .env file exists and source it
        env_file = Path(".env")
        if env_file.exists():
            logger.info("Found .env file, environment variables will be loaded by yarn")
        
        # Ensure modal-login directory exists
        modal_login_dir = Path("modal-login")
        if not modal_login_dir.exists():
            logger.error("modal-login directory not found!")
            return False
            
        # Check if package.json exists
        package_json = modal_login_dir / "package.json"
        if not package_json.exists():
            logger.error("package.json not found in modal-login directory!")
            return False
            
        return True
    
    def kill_existing_processes(self):
        """Kill any existing processes on port 3000."""
        logger.info("Checking for existing processes on port 3000...")
        
        # Use lsof to find processes on port 3000
        try:
            cmd = "lsof -ti :3000"
            process = Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            output, _ = process.communicate()
            
            if output.strip():
                logger.info("Killing existing processes on port 3000...")
                pids = output.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                        except (ProcessLookupError, ValueError):
                            pass
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Could not check/kill existing processes: {e}")
    
    def start_yarn_dev(self):
        """Start the yarn dev server."""
        logger.info("Starting yarn dev server...")
        
        # Change to modal-login directory and start yarn dev
        modal_login_dir = Path("modal-login")
        log_file = self.logs_dir / "yarn.log"
        
        try:
            # Set up environment
            env = os.environ.copy()
            
            # Source .env if it exists
            env_file = Path(".env")
            if env_file.exists():
                logger.info("Loading environment from .env file")
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env[key.strip()] = value.strip()
            
            # Start yarn dev process
            with open(log_file, 'w') as log:
                self.yarn_process = Popen(
                    ["yarn", "dev"],
                    cwd=modal_login_dir,
                    stdout=log,
                    stderr=log,
                    env=env
                )
            
            logger.info(f"Yarn dev server started with PID: {self.yarn_process.pid}")
            logger.info(f"Server logs are being written to: {log_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start yarn dev server: {e}")
            return False
    
    def wait_for_server_ready(self, timeout: int = 60):
        """Wait for the server to be ready by checking the log file."""
        logger.info("Waiting for server to be ready...")
        
        log_file = self.logs_dir / "yarn.log"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not log_file.exists():
                time.sleep(1)
                continue
                
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                # Look for indicators that the server is ready
                if any(indicator in content.lower() for indicator in [
                    "ready", "local:", "localhost:3000", "ready on"
                ]):
                    logger.info("✅ HTTP server is ready!")
                    return True
                    
            except Exception as e:
                logger.warning(f"Error reading log file: {e}")
            
            time.sleep(2)
        
        logger.warning("⚠️ Server readiness timeout - proceeding anyway")
        return False
    
    def monitor_user_data(self):
        """Monitor for user data files and log their status."""
        user_data_path = Path("modal-login/temp-data/userData.json")
        user_api_key_path = Path("modal-login/temp-data/userApiKey.json")
        
        logger.info("Monitoring for user authentication data...")
        
        while self.running:
            if user_data_path.exists():
                logger.info("✅ User data file found")
                if user_api_key_path.exists():
                    logger.info("✅ User API key file found")
                    logger.info("🎉 User authentication complete!")
                    break
            
            time.sleep(5)
    
    def start(self):
        """Start the HTTP server."""
        logger.info("Starting BlockAssist HTTP Server")
        
        if not self.setup_environment():
            logger.error("Environment setup failed")
            return False
        
        self.kill_existing_processes()
        
        if not self.start_yarn_dev():
            logger.error("Failed to start yarn dev server")
            return False
        
        self.running = True
        
        # Wait for server to be ready
        self.wait_for_server_ready()
        
        # Print status information
        print("\n" + "="*60)
        print("🚀 HTTP SERVER RUNNING")
        print("="*60)
        print(f"📍 Server URL: http://localhost:3000")
        print(f"📂 Logs: {self.logs_dir / 'yarn.log'}")
        print(f"🔧 Process PID: {self.yarn_process.pid}")
        print("="*60)
        print("\n💡 Instructions:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Complete the login process")
        print("3. The main BlockAssist process will detect when login is complete")
        print("4. Keep this process running until BlockAssist completes")
        print("\n⌨️  Press Ctrl+C to stop the server")
        print("="*60)
        
        # Start monitoring user data in background
        import threading
        monitor_thread = threading.Thread(target=self.monitor_user_data, daemon=True)
        monitor_thread.start()
        
        return True
    
    def stop(self):
        """Stop the HTTP server."""
        logger.info("Stopping HTTP server...")
        self.running = False
        
        if self.yarn_process and self.yarn_process.poll() is None:
            logger.info("Terminating yarn process...")
            self.yarn_process.terminate()
            
            # Wait a bit for graceful shutdown
            try:
                self.yarn_process.wait(timeout=5)
            except:
                logger.info("Force killing yarn process...")
                self.yarn_process.kill()
                self.yarn_process.wait()
        
        # Kill any remaining processes on port 3000
        self.kill_existing_processes()
        logger.info("HTTP server stopped")
    
    def run_forever(self):
        """Run the server until interrupted."""
        if not self.start():
            sys.exit(1)
        
        try:
            # Keep the process alive
            while self.running and (not self.yarn_process or self.yarn_process.poll() is None):
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()


def main():
    """Main entry point."""
    server = HTTPServerManager()
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        server.stop()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        server.run_forever()
    except Exception as e:
        logger.error(f"HTTP server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()