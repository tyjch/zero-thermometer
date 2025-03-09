#!/bin/bash

# setup.sh - Automated setup script for Zero Thermometer project
# This script configures a Raspberry Pi Zero 2 W with all necessary dependencies
# to run the zero-thermometer application

echo "Starting Zero Thermometer setup..."

# Update and install required packages
echo "Updating package lists..."
sudo apt update

echo "Installing required packages..."
sudo apt install -y \
  git \
  python3-virtualenv \
  fonts-dejavu \
  python3-pip \
  python3-setuptools \
  python3-dev \
  python3-smbus \
  python3-rpi.gpio

# Enable required interfaces
echo "Enabling I2C, SPI, and 1-Wire interfaces..."

# Check if config.txt exists in /boot/firmware/ (newer Raspberry Pi OS) or /boot/ (older versions)
if [ -f /boot/firmware/config.txt ]; then
  CONFIG_PATH="/boot/firmware/config.txt"
else
  CONFIG_PATH="/boot/config.txt"
fi

# Enable I2C
if ! grep -q "^dtparam=i2c_arm=on" $CONFIG_PATH; then
  echo "dtparam=i2c_arm=on" | sudo tee -a $CONFIG_PATH
fi

# Enable SPI
if ! grep -q "^dtparam=spi=on" $CONFIG_PATH; then
  echo "dtparam=spi=on" | sudo tee -a $CONFIG_PATH
fi

# Enable 1-Wire GPIO
if ! grep -q "^dtoverlay=w1-gpio" $CONFIG_PATH; then
  echo "dtoverlay=w1-gpio" | sudo tee -a $CONFIG_PATH
fi

# Load 1-Wire modules
sudo modprobe w1-gpio
sudo modprobe w1-therm

# Add modules to /etc/modules to load at boot
if ! grep -q "w1-gpio" /etc/modules; then
  echo "w1-gpio" | sudo tee -a /etc/modules
fi

if ! grep -q "w1-therm" /etc/modules; then
  echo "w1-therm" | sudo tee -a /etc/modules
fi

# Clone the repository if it doesn't exist
REPO_DIR="/home/admin/zero-thermometer"
if [ ! -d "$REPO_DIR" ]; then
  echo "Cloning repository..."
  git clone https://github.com/tyjch/zero-thermometer.git $REPO_DIR
else
  echo "Repository already exists. Pulling latest changes..."
  cd $REPO_DIR
  git pull
fi

# Setup virtual environment
cd $REPO_DIR
echo "Setting up virtual environment..."
python3 -m virtualenv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create systemd service for autostarting the application
echo "Creating systemd service..."
cat << EOF | sudo tee /etc/systemd/system/zero-thermometer.service
[Unit]
Description=Zero Thermometer Service
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=$REPO_DIR
ExecStart=$REPO_DIR/venv/bin/python $REPO_DIR/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "Enabling and starting the service..."
sudo systemctl enable zero-thermometer.service
sudo systemctl start zero-thermometer.service

echo "Setup complete! The Zero Thermometer service is now running."