"""Daemon that watches logs for BUILD FAILED or Python tracebacks and crashes on detection."""

import logging
import os
import re
import threading
import time
from pathlib import Path
from subprocess import Popen
from typing import Dict, List

logger = logging.getLogger(__name__)

PROCESSES: List[Popen] = []


def kill_gradle_processes():
    logging.info("Running kill_gradle_processes")
    # First try regular kill
    cmd = "pkill -f gradle"
    process = Popen(cmd, shell=True)
    process.wait()
    
    # Force kill any remaining gradle processes
    cmd_force = "pkill -9 -f gradle"
    process_force = Popen(cmd_force, shell=True)
    process_force.wait()


def kill_dev_servers():
    """Kill development servers (Next.js, yarn dev, etc.)"""
    logging.info("Running kill_dev_servers")
    # Kill Next.js development servers
    cmd_next = "pkill -f 'next-server'"
    process_next = Popen(cmd_next, shell=True)
    process_next.wait()
    
    # Kill yarn dev processes
    cmd_yarn = "pkill -f 'yarn dev'"
    process_yarn = Popen(cmd_yarn, shell=True)
    process_yarn.wait()
    
    # Force kill any remaining dev server processes
    cmd_next_force = "pkill -9 -f 'next-server'"
    process_next_force = Popen(cmd_next_force, shell=True)
    process_next_force.wait()
    
    cmd_yarn_force = "pkill -9 -f 'yarn dev'"
    process_yarn_force = Popen(cmd_yarn_force, shell=True)
    process_yarn_force.wait()


def cleanup_processes(processes=PROCESSES):
    logging.info("Running cleanup_processes")
    print("Cleaning up processes...")
    kill_gradle_processes()
    kill_dev_servers()
    
    # Kill any blockassist processes (including training)
    cmd_blockassist = "pkill -f -i blockassist"
    process_blockassist = Popen(cmd_blockassist, shell=True)
    process_blockassist.wait()
    
    # Force kill any remaining blockassist processes
    cmd_blockassist_force = "pkill -9 -f -i blockassist"
    process_blockassist_force = Popen(cmd_blockassist_force, shell=True)
    process_blockassist_force.wait()
    
    # Kill processes from the PROCESSES list
    for proc in processes:
        if proc.poll() is None:  # Process is still running
            try:
                # Try graceful termination first
                proc.terminate()
                proc.wait(timeout=3)
            except:
                # Force kill if graceful termination fails
                try:
                    proc.kill()
                    proc.wait()
                except:
                    pass


class LogWatcherDaemon:
    SEPARATOR = "=" * 60

    def __init__(self, logs_dir: str = "logs", check_interval: float = 1.0):
        self.logs_dir = Path(logs_dir)
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.file_positions: Dict[str, int] = {}
        self.build_failed_pattern = re.compile(r"BUILD FAILED", re.IGNORECASE)
        self.traceback_pattern = re.compile(
            r"Traceback \(most recent call last\):", re.IGNORECASE
        )

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._watch_logs, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _watch_logs(self):
        while self.running:
            try:
                self._check_log_files()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"LogWatcher error: {e}")
                time.sleep(self.check_interval)

    def _analyze_log_content(self, log_type: str, log_file: Path, content: str):
        lines = content.split("\n")
        if log_type == "malmo":
            self._check_malmo_errors(log_file, lines)
        elif log_type == "blockassist":
            self._check_blockassist_errors(log_file, lines)

    def _check_log_files(self):
        self._check_malmo_logs()
        self._check_blockassist_logs()

    def _check_malmo_logs(self):
        malmo_log = self.logs_dir / "malmo.log"
        if malmo_log.exists():
            self._check_log_file("malmo", malmo_log)

    def _check_blockassist_logs(self):
        for log_file in self.logs_dir.glob("blockassist*.log"):
            self._check_log_file("blockassist", log_file)

    def _check_log_file(self, log_type: str, log_file: Path):
        file_path = str(log_file)
        try:
            current_size = log_file.stat().st_size
            last_position = self.file_positions.get(file_path, 0)

            if current_size < last_position:
                last_position = 0
            if current_size <= last_position:
                return

            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(last_position)
                new_content = f.read()

            self.file_positions[file_path] = current_size
            self._analyze_log_content(log_type, log_file, new_content)

        except (OSError, IOError):
            pass

    def _check_malmo_errors(self, log_file: Path, lines: list):
        build_failed = any(self.build_failed_pattern.search(line) for line in lines)
        traceback = self._find_traceback(lines)
        if build_failed or traceback:
            error_msg = f"CRITICAL ERROR IN {log_file}: "
            self._crash_process(error_msg, traceback)

    def _check_blockassist_errors(self, log_file: Path, lines: list):
        traceback = self._find_traceback(lines)
        if traceback:
            error_msg = f"CRITICAL ERROR IN {log_file}:"
            self._crash_process(error_msg, traceback)

    def _find_traceback(self, lines: list):
        traceback_lines = []
        in_traceback = False

        for line in lines:
            if self.traceback_pattern.search(line):
                in_traceback = True
                traceback_lines = [line]
            elif in_traceback:
                traceback_lines.append(line)
                if (
                    line.strip()
                    and not line.startswith((" ", "\t"))
                    and any(
                        exc in line
                        for exc in ["Error:", "Exception:", "Error", "Exception"]
                    )
                ):
                    return traceback_lines


        allowed = ("KeyboardInterrupt")
        if in_traceback and traceback_lines:
            if traceback_lines[-1] in allowed:
                return None

        return traceback_lines if in_traceback else None

    def _crash_process(self, error_msg: str, traceback_lines=None):
        print(f"\n{self.SEPARATOR}")
        print(f"║{'DAEMON DETECTED CRITICAL ERROR'.center(58)}║")
        print(self.SEPARATOR)
        print(f"║ {error_msg:<56} ║")
        if traceback_lines:
            for line in traceback_lines:
                # Truncate long lines to fit within the box
                truncated_line = line[:56] if len(line) > 56 else line
                print(f"║ {truncated_line:<56} ║")
        print(f"║ {'Process will be terminated.':<56} ║")
        print(self.SEPARATOR)

        cleanup_processes()
        time.sleep(1)
        os._exit(1)


# Global daemon instance
_LOG_DAEMON = None


def start_log_watcher(logs_dir: str = "logs", check_interval: float = 1.0):
    global _LOG_DAEMON
    if _LOG_DAEMON is None:
        _LOG_DAEMON = LogWatcherDaemon(logs_dir, check_interval)
    _LOG_DAEMON.start()


def stop_log_watcher():
    global _LOG_DAEMON
    if _LOG_DAEMON is not None:
        _LOG_DAEMON.stop()
