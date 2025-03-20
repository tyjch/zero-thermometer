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

def enable_i2c():
    """Enable I2C interface"""
    print("Enabling I2C interface...")
    
    # Check if I2C is already enabled
    if "i2c_arm=on" in utils.run_command("grep 'i2c_arm=on' /boot/config.txt", check=False):
        print("I2C is already enabled.")
        return
    
    # Enable I2C in config.txt if not already enabled
    utils.run_command("raspi-config nonint do_i2c 0")
    
    # Load I2C kernel module
    utils.run_command("modprobe i2c-dev")
    utils.run_command("echo 'i2c-dev' >> /etc/modules")
    
    print("I2C interface enabled successfully.")

def enable_spi():
    """Enable SPI interface"""
    print("Enabling SPI interface...")
    
    # Check if SPI is already enabled
    if "spi=on" in utils.run_command("grep 'spi=on' /boot/config.txt", check=False):
        print("SPI is already enabled.")
        return
    
    # Enable SPI in config.txt if not already enabled
    utils.run_command("raspi-config nonint do_spi 0")
    
    print("SPI interface enabled successfully.")

def enable_1wire():
    """Enable 1-Wire interface"""
    print("Enabling 1-Wire interface...")
    
    # Check if 1-Wire is already enabled
    if "dtoverlay=w1-gpio" in utils.run_command("grep 'dtoverlay=w1-gpio' /boot/config.txt", check=False):
        print("1-Wire is already enabled.")
        return
    
    # Add dtoverlay for 1-Wire to config.txt
    utils.run_command("echo 'dtoverlay=w1-gpio' >> /boot/config.txt")
    
    # Load 1-Wire kernel modules
    utils.run_command("modprobe w1-gpio")
    utils.run_command("modprobe w1-therm")
    utils.run_command("echo 'w1-gpio' >> /etc/modules")
    utils.run_command("echo 'w1-therm' >> /etc/modules")
    
    print("1-Wire interface enabled successfully.")

def main():
    """Main function to set up interfaces"""
    # Check for sudo privileges
    utils.check_sudo()
    
    # Check if running on a Raspberry Pi
    if not utils.is_raspberry_pi():
        print("This script must be run on a Raspberry Pi.")
        print("Skipping interface setup.")
        return
    
    print("Setting up Raspberry Pi interfaces...")
    
    # Enable interfaces
    enable_i2c()
    enable_spi()
    enable_1wire()
    
    print("Interface setup completed successfully!")
    print("NOTE: A reboot may be required for changes to take effect.")
    
    # Ask for reboot
    reboot = input("Would you like to reboot now? [y/N]: ").lower()
    if reboot == 'y':
        print("Rebooting...")
        utils.run_command("reboot")

if __name__ == "__main__":
    main()