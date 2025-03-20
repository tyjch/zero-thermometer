#!/usr/bin/env python3
import os
import sys
import argparse
import importlib.util
from pathlib import Path

# Load utilities
script_dir = Path(__file__).parent.absolute()
utils_path = script_dir / "scripts" / "utils.py"

if not utils_path.exists():
    # Create scripts directory if it doesn't exist
    (script_dir / "scripts").mkdir(exist_ok=True)
    print("Error: utils.py not found. Please ensure it exists in the scripts directory.")
    sys.exit(1)

# Import utils module
spec  = importlib.util.spec_from_file_location("utils", utils_path)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)

def get_install_config():
    """Get installation configuration"""
    # Get current user
    current_user = utils.get_current_user()
    
    # Set installation directory
    install_dir = os.environ.get('INSTALL_DIR', f"/home/{current_user}/zero-thermometer")
    
    # Check if running as root or with sudo
    is_root = os.geteuid() == 0
    
    return current_user, install_dir, is_root

def show_config(current_user, install_dir):
    """Show current configuration"""
    print("=== Zero Thermometer Installation ===")
    print("Current configuration:")
    print(f"- Installation directory: {install_dir}")
    print(f"- User: {current_user}")
    
    if utils.is_raspberry_pi():
        print(f"- Hardware: {utils.detect_pi_model()}")
    else:
        print("- Hardware: Not a Raspberry Pi (some features might not work)")
    print("")

def get_user_config(current_user, install_dir, is_root):
    """Get user configuration preferences"""
    change = input("Would you like to change these settings? [y/N]: ").lower()
    
    if change == 'y':
        custom_dir = input(f"Installation directory [{install_dir}]: ")
        if custom_dir:
            install_dir = custom_dir
        
        # Only ask about current user if running as root or sudo
        if is_root:
            custom_user = input(f"User to run services [{current_user}]: ")
            if custom_user:
                current_user = custom_user
    
    return current_user, install_dir

def run_component_script(script_name, current_user, install_dir):
    """Run a component installation script"""
    script_path = script_dir / "scripts" / f"{script_name}.py"
    
    if not script_path.exists():
        print(f"Error: {script_name}.py not found")
        return False
    
    # Set environment variables for the script
    os.environ['CURRENT_USER'] = current_user
    os.environ['INSTALL_DIR'] = install_dir
    
    # Import and run the script
    try:
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Call the main function if it exists
        if hasattr(module, 'main'):
            module.main()
        
        return True
    except Exception as e:
        print(f"Error running {script_name}.py: {e}")
        return False

def main():
    # Get installation configuration
    current_user, install_dir, is_root = get_install_config()
    
    # Show current configuration
    show_config(current_user, install_dir)
    
    # Get user configuration preferences
    current_user, install_dir = get_user_config(current_user, install_dir, is_root)
    
    # Menu for component selection
    print("")
    print("What components would you like to install?")
    print("1) Core system dependencies")
    print("2) Raspberry Pi interfaces (I2C, SPI, 1-Wire)")
    print("3) Zero Thermometer application")
    print("4) GitHub Actions Runner")
    print("5) All of the above")
    print("6) Exit")
    
    choice = input("Enter your choice [5]: ") or "5"
    
    if choice == "1":
        run_component_script("install_dependencies", current_user, install_dir)
    elif choice == "2":
        run_component_script("setup_interfaces", current_user, install_dir)
    elif choice == "3":
        run_component_script("install_app", current_user, install_dir)
    elif choice == "4":
        run_component_script("install_github_runner", current_user, install_dir)
    elif choice == "5":
        print("Installing all components...")
        run_component_script("install_dependencies", current_user, install_dir)
        run_component_script("setup_interfaces", current_user, install_dir)
        run_component_script("install_app", current_user, install_dir)
        run_component_script("install_github_runner", current_user, install_dir)
    elif choice == "6":
        print("Exiting setup.")
        sys.exit(0)
    else:
        print("Invalid option. Exiting.")
        sys.exit(1)
    
    print("Setup completed successfully!")

if __name__ == "__main__":
    # Check if running as root when not explicitly skipping the check
    if "--no-sudo-check" not in sys.argv and os.geteuid() != 0:
        utils.check_sudo()
    
    main()