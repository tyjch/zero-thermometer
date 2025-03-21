#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

# Import utils if running as standalone script
if __name__ == "__main__":
    script_dir = Path(__file__).parent.absolute()
    utils_path = script_dir / "utils.py"
    
    if not utils_path.exists():
        print("Error: utils.py not found. Please run the main setup.py script.")
        sys.exit(1)
    
    sys.path.append(str(script_dir))
    import utils
else:
    # Utils is already imported by the parent script
    from scripts import utils

def install_system_packages():
    """Install required system packages"""
    print("Installing system dependencies...")
    
    # Update package lists
    utils.run_command("apt-get update")
    
    # Install required packages
    packages = [
        "python3-venv",
        "python3-dev",
        # "libjpeg-dev",
        # "zlib1g-dev",
        # "libopenjp2-7",
        # "libtiff-dev",
        # "libatlas-base-dev",
        "i2c-tools",
        "git"
    ]
    
    utils.run_command(f"apt-get install -y {' '.join(packages)}")
    print("System packages installed successfully.")

def setup_python_environment(install_dir, current_user):
    """Set up Python virtual environment"""
    print("Setting up Python virtual environment...")
    
    # Create installation directory if it doesn't exist
    utils.create_directory(install_dir, current_user)
    
    # Create virtual environment
    venv_path = Path(install_dir) / "venv"
    if not venv_path.exists():
        utils.run_command(f"python3 -m venv {venv_path}")
        
        # Fix ownership
        utils.run_command(f"chown -R {current_user}:{current_user} {venv_path}")
        
        print(f"Virtual environment created at {venv_path}")
    else:
        print(f"Virtual environment already exists at {venv_path}")

    # Upgrade pip
    utils.run_command(f"{venv_path}/bin/pip install --upgrade pip")
    
    print("Python environment set up successfully.")

def main():
    """Main function to install dependencies"""
    # Check for sudo privileges
    utils.check_sudo()
    
    # Get environment variables
    current_user = os.environ.get('CURRENT_USER') or utils.get_current_user()
    install_dir = os.environ.get('INSTALL_DIR') or f"/home/{current_user}/zero-thermometer"
    
    print(f"Installing dependencies for user {current_user} in {install_dir}...")
    
    # Install system packages
    install_system_packages()
    
    # Set up Python environment
    setup_python_environment(install_dir, current_user)
    
    print("Dependency installation completed successfully!")

if __name__ == "__main__":
    main()