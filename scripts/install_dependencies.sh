#!/bin/bash
# install_dependencies.sh - Install required system packages

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

echo "Installing system dependencies..."

# Check if running with sudo
check_sudo

# Detect package manager
if command -v apt &> /dev/null; then
  PKG_MANAGER="apt"
elif command -v apt-get &> /dev/null; then
  PKG_MANAGER="apt-get"
elif command -v yum &> /dev/null; then
  PKG_MANAGER="yum"
elif command -v dnf &> /dev/null; then
  PKG_MANAGER="dnf"
else
  echo "Warning: No supported package manager found (apt, apt-get, yum, dnf)."
  echo "You may need to install required packages manually."
  
  read -p "Continue with setup? [y/N]: " continue_setup
  if [[ ! "$continue_setup" =~ ^[Yy]$ ]]; then
    echo "Setup aborted."
    exit 0
  fi
  
  PKG_MANAGER="echo" # Will just echo the packages that would be installed
fi

# Update package lists
echo "Updating package lists..."
if [ "$PKG_MANAGER" = "apt" ] || [ "$PKG_MANAGER" = "apt-get" ]; then
  $PKG_MANAGER update
elif [ "$PKG_MANAGER" = "yum" ] || [ "$PKG_MANAGER" = "dnf" ]; then
  $PKG_MANAGER check-update || true  # Don't fail if no updates available
fi

# Define packages based on package manager
if [ "$PKG_MANAGER" = "apt" ] || [ "$PKG_MANAGER" = "apt-get" ]; then
  PACKAGE_LIST="git python3-virtualenv fonts-dejavu python3-pip python3-setuptools python3-dev curl jq"
  
  # Only install Raspberry Pi specific packages if we're on a Pi
  if is_raspberry_pi; then
    PACKAGE_LIST="$PACKAGE_LIST python3-smbus python3-rpi.gpio"
  fi
elif [ "$PKG_MANAGER" = "yum" ] || [ "$PKG_MANAGER" = "dnf" ]; then
  PACKAGE_LIST="git python3-virtualenv dejavu-sans-fonts python3-pip python3-setuptools python3-devel curl jq"
else
  PACKAGE_LIST="git python3-virtualenv python3-pip python3-setuptools python3-dev curl jq"
fi

# Install essential packages
echo "Installing required packages: $PACKAGE_LIST"
$PKG_MANAGER install -y $PACKAGE_LIST

echo "System dependencies installed successfully."