#!/usr/bin/env python3
"""
BlockAssist Launcher
This script provides an easy way to run BlockAssist with separated processes for better WSL compatibility.
"""

import argparse
import sys
import subprocess
from pathlib import Path


def run_http_server_only():
    """Run only the HTTP server for testing or development."""
    print("🚀 Starting BlockAssist HTTP Server only...")
    print("📍 Server will be available at: http://localhost:3000")
    print("⌨️  Press Ctrl+C to stop")
    
    try:
        subprocess.run([sys.executable, "run_http_server.py"])
    except KeyboardInterrupt:
        print("\n👋 HTTP server stopped")


def run_full_application():
    """Run the full BlockAssist application with separated processes."""
    print("🚀 Starting full BlockAssist application...")
    print("📝 HTTP server will run in a separate process for better WSL compatibility")
    
    try:
        subprocess.run([sys.executable, "run.py"])
    except KeyboardInterrupt:
        print("\n👋 BlockAssist stopped")


def main():
    parser = argparse.ArgumentParser(
        description="BlockAssist Launcher - Run with separated processes for WSL compatibility"
    )
    parser.add_argument(
        "--http-only",
        action="store_true",
        help="Run only the HTTP server (for testing or development)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="BlockAssist Launcher 1.0"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("run.py").exists() or not Path("run_http_server.py").exists():
        print("❌ Error: Please run this script from the BlockAssist root directory")
        print("   Make sure both run.py and run_http_server.py exist")
        sys.exit(1)
    
    print("=" * 60)
    print("🎮 BLOCKASSIST LAUNCHER")
    print("=" * 60)
    print("🔧 WSL-Compatible Process Separation Enabled")
    print("=" * 60)
    
    if args.http_only:
        run_http_server_only()
    else:
        run_full_application()


if __name__ == "__main__":
    main()