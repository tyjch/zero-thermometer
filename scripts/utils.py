#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from pathlib import Path

def check_sudo():
    """Check if script is running with sudo/root privileges"""
    if os.geteuid() != 0:
        print("This script must be run with sudo or as root.")
        print("Please run: sudo python3 setup.py")
        sys.exit(1)

def is_raspberry_pi():
    """Check if we're running on a Raspberry Pi"""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
        return 'Raspberry Pi' in model
    except:
        return False

def detect_pi_model():
    """Detect Raspberry Pi model"""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            return f.read().strip('\0')
    except:
        return "Unknown"

def run_command(cmd, check=True):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, text=True, 
                               capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}")
        print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e.stderr

def get_current_user():
    """Get the current user (non-root) even when running as sudo"""
    if 'SUDO_USER' in os.environ:
        return os.environ['SUDO_USER']
    else:
        try:
            user = run_command("who am i | awk '{print $1}'")
            if user:
                return user
        except:
            pass
    
    return os.getlogin()

def create_directory(path, owner=None):
    """Create directory if it doesn't exist and set owner"""
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)
        print(f"Created directory: {path}")
    
    if owner:
        run_command(f"chown -R {owner}:{owner} {path}")