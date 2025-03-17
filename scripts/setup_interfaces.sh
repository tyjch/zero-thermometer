#!/bin/bash
# setup_interfaces.sh - Configure Raspberry Pi hardware interfaces

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

echo "Setting up Raspberry Pi hardware interfaces..."

# Check if running with sudo
check_sudo

# Verify we're on a Raspberry Pi
if ! is_raspberry_pi; then
  echo "Warning: This doesn't appear to be a Raspberry Pi."
  echo "Hardware interface setup may not work correctly."
  read -p "Continue anyway? [y/N]: " continue_setup
  if [[ ! "$continue_setup" =~ ^[Yy]$ ]]; then
    echo "Setup aborted."
    exit 0
  fi
fi

# Display Pi model
PI_MODEL=$(detect_pi_model)
echo "Detected hardware: $PI_MODEL"

# Check if config.txt exists in /boot/firmware/ (newer Raspberry Pi OS) or /boot/ (older versions)
if [ -f /boot/firmware/config.txt ]; then
  CONFIG_PATH="/boot/firmware/config.txt"
else
  CONFIG_PATH="/boot/config.txt"
fi

echo "Found config file at: $CONFIG_PATH"

# Enable I2C
if ! grep -q "^dtparam=i2c_arm=on" $CONFIG_PATH; then
  echo "Enabling I2C interface..."
  echo "dtparam=i2c_arm=on" | tee -a $CONFIG_PATH
else
  echo "I2C interface already enabled"
fi

# Enable SPI
if ! grep -q "^dtparam=spi=on" $CONFIG_PATH; then
  echo "Enabling SPI interface..."
  echo "dtparam=spi=on" | tee -a $CONFIG_PATH
else
  echo "SPI interface already enabled"
fi

# Enable 1-Wire GPIO
if ! grep -q "^dtoverlay=w1-gpio" $CONFIG_PATH; then
  echo "Enabling 1-Wire interface..."
  echo "dtoverlay=w1-gpio" | tee -a $CONFIG_PATH
else
  echo "1-Wire interface already enabled"
fi

# Load modules
echo "Loading kernel modules..."
modprobe w1-gpio || echo "Warning: Failed to load w1-gpio module, may need a reboot"
modprobe w1-therm || echo "Warning: Failed to load w1-therm module, may need a reboot"

# Add modules to /etc/modules to load at boot
if ! grep -q "w1-gpio" /etc/modules; then
  echo "Adding w1-gpio to /etc/modules..."
  echo "w1-gpio" | tee -a /etc/modules
fi

if ! grep -q "w1-therm" /etc/modules; then
  echo "Adding w1-therm to /etc/modules..."
  echo "w1-therm" | tee -a /etc/modules
fi

echo "Hardware interfaces configured successfully."
echo "Note: A reboot is recommended for changes to take full effect."