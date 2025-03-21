#!/usr/bin/env python3
import os
import sys
import argparse
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

def create_systemd_service(install_dir=None, current_user=None):
    """Create and enable systemd service for zero-thermometer"""
    # Check for sudo privileges
    utils.check_sudo()
    
    # Get current user if not provided
    if current_user is None:
        current_user = os.environ.get('CURRENT_USER') or utils.get_current_user()
    
    # Get installation directory if not provided
    if install_dir is None:
        install_dir = os.environ.get('INSTALL_DIR') or f"/home/{current_user}/zero-thermometer"
    
    # Ensure the directory exists
    install_path = Path(install_dir)
    if not install_path.exists():
        print(f"Error: Installation directory {install_dir} does not exist.")
        print("Please specify a valid installation directory.")
        return False
    
    print(f"Creating systemd service for user {current_user} in {install_dir}...")
    
    # Define service file path
    service_file = "/etc/systemd/system/zero-thermometer.service"
    
    # Create service file content
    service_content = f"""[Unit]
Description=Zero Thermometer Service
After=network.target

[Service]
Type=simple
User={current_user}
WorkingDirectory={install_dir}
ExecStart={install_dir}/venv/bin/python {install_dir}/main.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

    # Write service file
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        # Set proper permissions
        utils.run_command(f"chmod 644 {service_file}")
        
        # Reload systemd
        utils.run_command("systemctl daemon-reload")
        
        # Enable the service
        utils.run_command("systemctl enable zero-thermometer.service")
        
        print("Systemd service created and enabled.")
        
        # Ask if user wants to start the service
        start_service = input("Would you like to start the service now? [y/N]: ").lower()
        if start_service == 'y':
            utils.run_command("systemctl start zero-thermometer.service")
            print("Service started. Check status with: systemctl status zero-thermometer.service")
        
        return True
    
    except Exception as e:
        print(f"Error creating systemd service: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Install Zero Thermometer systemd service")
    parser.add_argument("--user", help="User to run the service as")
    parser.add_argument("--dir", help="Installation directory path")
    
    args = parser.parse_args()
    
    # If arguments were provided, use them
    user = args.user
    directory = args.dir
    
    # If no arguments, prompt for values
    if not user:
        user = input(f"User to run the service as [{utils.get_current_user()}]: ")
        user = user or utils.get_current_user()
    
    if not directory:
        default_dir = f"/home/{user}/zero-thermometer"
        directory = input(f"Installation directory [{default_dir}]: ")
        directory = directory or default_dir
    
    # Create the service
    create_systemd_service(directory, user)

if __name__ == "__main__":
    main()