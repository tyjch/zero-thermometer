#!/usr/bin/env python3
import os
import sys
import shutil
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

def create_systemd_service(install_dir, current_user):
    """Create and enable systemd service"""
    print("Creating systemd service...")
    
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
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    # Set proper permissions
    utils.run_command(f"chmod 644 {service_file}")
    
    # Reload systemd, enable and start the service
    utils.run_command("systemctl daemon-reload")
    utils.run_command("systemctl enable zero-thermometer.service")
    
    print("Systemd service created and enabled.")

def install_application(install_dir, current_user):
    """Install the Zero Thermometer application"""
    print("Installing Zero Thermometer application...")
    
    # Create installation directory if it doesn't exist
    install_path = Path(install_dir)
    utils.create_directory(install_path, current_user)
    
    # Determine source directory (current script's parent directory)
    source_dir = Path(__file__).parent.parent.absolute()
    
    # Copy application files
    for item in ['main.py', 'sampler.py', 'requirements.txt', '.env.example', 'clients', 'display', 'sensors', 'monitor']:
        src_path = source_dir / item
        dst_path = install_path / item
        
        if src_path.exists():
            if src_path.is_dir():
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
    
    # Create logs directory
    log_dir = install_path / "logs"
    utils.create_directory(log_dir, current_user)
    
    # Set proper permissions
    utils.run_command(f"chown -R {current_user}:{current_user} {install_path}")
    utils.run_command(f"chmod -R 755 {install_path}")
    utils.run_command(f"chmod -R 777 {log_dir}")  # Writable log directory
    
    # Create .env file if it doesn't exist
    env_file = install_path / ".env"
    env_example = install_path / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)
        utils.run_command(f"chown {current_user}:{current_user} {env_file}")
        utils.run_command(f"chmod 640 {env_file}")
        print("Created initial .env file from example.")
    
    # Install Python dependencies
    venv_pip = install_path / "venv" / "bin" / "pip"
    if venv_pip.exists():
        utils.run_command(f"{venv_pip} install -r {install_path}/requirements.txt")
        print("Installed Python dependencies.")
    else:
        print("Warning: Virtual environment not found. Please run the dependencies script first.")
    
    print("Zero Thermometer application installed successfully.")

def main():
    """Main function to install the application"""
    # Check for sudo privileges
    utils.check_sudo()
    
    # Get environment variables
    current_user = os.environ.get('CURRENT_USER') or utils.get_current_user()
    install_dir = os.environ.get('INSTALL_DIR') or f"/home/{current_user}/zero-thermometer"
    
    print(f"Installing Zero Thermometer for user {current_user} in {install_dir}...")
    
    # Install application
    install_application(install_dir, current_user)
    
    # Create systemd service
    create_systemd_service(install_dir, current_user)
    
    # Ask if user wants to start the service
    start_service = input("Would you like to start the service now? [y/N]: ").lower()
    if start_service == 'y':
        utils.run_command("systemctl start zero-thermometer.service")
        print("Service started. Check status with: systemctl status zero-thermometer.service")
    
    print("Installation completed successfully!")
    print("\nNEXT STEPS:")
    print(f"1. Edit the .env file with your configuration: sudo nano {install_dir}/.env")
    print("2. Start the service if not already started: sudo systemctl start zero-thermometer.service")
    print("3. Check service status: sudo systemctl status zero-thermometer.service")
    print("4. View logs: sudo journalctl -u zero-thermometer.service -f")

if __name__ == "__main__":
    main()