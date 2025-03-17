#!/bin/bash
# setup.sh - Main installer for Zero Thermometer project
# This script coordinates the installation of different components

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get current user
CURRENT_USER=$(who am i | awk '{print $1}')
[ "$CURRENT_USER" = "" ] && CURRENT_USER=$(whoami)

# Set installation directory
INSTALL_DIR=${INSTALL_DIR:-"/home/$CURRENT_USER/zero-thermometer"}

# Export for child scripts
export INSTALL_DIR

echo "Starting Zero Thermometer setup..."

# Source utility functions
source "$SCRIPT_DIR/scripts/utils.sh"

# Create scripts directory if running from repo root
mkdir -p "$SCRIPT_DIR/scripts"

# Check if running as root or with sudo
check_sudo

# Show current configuration
echo "=== Zero Thermometer Installation ==="
echo "Current configuration:"
echo "- Installation directory: $INSTALL_DIR"
echo "- User: $CURRENT_USER"
if is_raspberry_pi; then
  echo "- Hardware: $(detect_pi_model)"
else
  echo "- Hardware: Not a Raspberry Pi (some features might not work)"
fi
echo ""

# Prompt to change settings
read -p "Would you like to change these settings? [y/N]: " change_settings
if [[ "$change_settings" =~ ^[Yy]$ ]]; then
  read -p "Installation directory [$INSTALL_DIR]: " custom_dir
  INSTALL_DIR=${custom_dir:-$INSTALL_DIR}
  export INSTALL_DIR
  
  # Only ask about current user if running as root or sudo
  if [ "$EUID" -eq 0 ]; then
    read -p "User to run services [$CURRENT_USER]: " custom_user
    CURRENT_USER=${custom_user:-$CURRENT_USER}
    export CURRENT_USER
  fi
fi

echo ""
echo "What components would you like to install?"
echo "1) Core system dependencies"
echo "2) Raspberry Pi interfaces (I2C, SPI, 1-Wire)"
echo "3) Zero Thermometer application"
echo "4) GitHub Actions Runner"
echo "5) All of the above"
echo "6) Exit"
read -p "Enter your choice [5]: " choice
choice=${choice:-5}  # Default to option 5

case $choice in
  1)
    bash "$SCRIPT_DIR/scripts/install_dependencies.sh"
    ;;
  2)
    bash "$SCRIPT_DIR/scripts/setup_interfaces.sh"
    ;;
  3)
    bash "$SCRIPT_DIR/scripts/install_app.sh"
    ;;
  4)
    bash "$SCRIPT_DIR/scripts/install_github_runner.sh"
    ;;
  5)
    echo "Installing all components..."
    bash "$SCRIPT_DIR/scripts/install_dependencies.sh"
    bash "$SCRIPT_DIR/scripts/setup_interfaces.sh"
    bash "$SCRIPT_DIR/scripts/install_app.sh"
    bash "$SCRIPT_DIR/scripts/install_github_runner.sh"
    ;;
  6)
    echo "Exiting setup."
    exit 0
    ;;
  *)
    echo "Invalid option. Exiting."
    exit 1
    ;;
esac

echo "Setup completed successfully!"