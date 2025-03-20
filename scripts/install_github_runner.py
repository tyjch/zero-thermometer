#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import shutil
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

def download_github_runner():
    """Download the latest GitHub Actions runner"""
    print("Downloading GitHub Actions runner...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Detect architecture
        arch = utils.run_command("uname -m")
        
        # Determine runner version based on architecture
        if arch == "armv7l" or arch == "armhf":
            # ARM 32-bit (Raspberry Pi 2/3/4/Zero 2W with 32-bit OS)
            runner_url = "https://github.com/actions/runner/releases/download/v2.310.2/actions-runner-linux-arm-2.310.2.tar.gz"
        elif arch == "aarch64" or arch == "arm64":
            # ARM 64-bit (Raspberry Pi 3/4/5/Zero 2W with 64-bit OS)
            runner_url = "https://github.com/actions/runner/releases/download/v2.310.2/actions-runner-linux-arm64-2.310.2.tar.gz"
        elif arch == "x86_64":
            # x86_64 (Standard PC)
            runner_url = "https://github.com/actions/runner/releases/download/v2.310.2/actions-runner-linux-x64-2.310.2.tar.gz"
        else:
            print(f"Unsupported architecture: {arch}")
            return None
        
        # Download runner
        print(f"Downloading runner for {arch} architecture...")
        utils.run_command(f"wget -q -O {temp_path}/runner.tar.gz {runner_url}")
        
        return f"{temp_path}/runner.tar.gz"

def install_github_runner(runner_file, install_dir, current_user):
    """Install GitHub Actions runner"""
    print("Installing GitHub Actions runner...")
    
    # Create runner directory
    runner_dir = Path(install_dir) / "github-runner"
    utils.create_directory(runner_dir, current_user)
    
    # Extract runner
    utils.run_command(f"tar xzf {runner_file} -C {runner_dir}")
    
    # Set permissions
    utils.run_command(f"chown -R {current_user}:{current_user} {runner_dir}")
    utils.run_command(f"chmod -R 755 {runner_dir}")
    
    # Install dependencies
    utils.run_command(f"cd {runner_dir} && ./bin/installdependencies.sh")
    
    print("GitHub Actions runner installed successfully.")
    return runner_dir

def configure_github_runner(runner_dir, current_user):
    """Configure GitHub Actions runner"""
    print("\nGitHub Actions runner is now installed.")
    print("To configure it, you need a GitHub token and repository URL.")
    print("Get these from your GitHub repository: Settings -> Actions -> Runners -> New self-hosted runner")
    
    configure = input("Would you like to configure the runner now? [y/N]: ").lower()
    if configure != 'y':
        print("Skipping configuration. You can configure later with:")
        print(f"cd {runner_dir} && ./config.sh --url YOUR_REPO_URL --token YOUR_TOKEN")
        return
    
    # Get configuration details
    repo_url = input("Enter your GitHub repository URL: ")
    token = input("Enter your GitHub token: ")
    runner_name = input("Enter a name for this runner [default: hostname]: ") or utils.run_command("hostname")
    
    # Configure runner
    utils.run_command(
        f"cd {runner_dir} && su {current_user} -c './config.sh --url {repo_url} --token {token} --name {runner_name} --unattended'",
        check=False
    )
    
    # Create systemd service
    service_file = "/etc/systemd/system/github-runner.service"
    service_content = f"""[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
ExecStart={runner_dir}/run.sh
User={current_user}
WorkingDirectory={runner_dir}
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=5min
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

    with open(service_file, 'w') as f:
        f.write(service_content)
    
    # Set permissions and enable service
    utils.run_command(f"chmod 644 {service_file}")
    utils.run_command("systemctl daemon-reload")
    utils.run_command("systemctl enable github-runner.service")
    utils.run_command("systemctl start github-runner.service")
    
    print("GitHub Actions runner configured and service started.")
    print("Check status with: systemctl status github-runner.service")

def main():
    """Main function to install GitHub Actions runner"""
    # Check for sudo privileges
    utils.check_sudo()
    
    # Get environment variables
    current_user = os.environ.get('CURRENT_USER') or utils.get_current_user()
    install_dir  = os.environ.get('INSTALL_DIR') or f"/home/{current_user}/zero-thermometer"
    
    print(f"Installing GitHub Actions runner for user {current_user} in {install_dir}...")
    
    # Download runner
    runner_file = download_github_runner()
    if not runner_file:
        print("Failed to download GitHub Actions runner.")
        return
    
    # Install runner
    runner_dir = install_github_runner(runner_file, install_dir, current_user)
    
    # Configure runner
    configure_github_runner(runner_dir, current_user)
    
    print("GitHub Actions runner installation completed!")

if __name__ == "__main__":
    main()