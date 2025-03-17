#!/bin/bash
# utils.sh - Common utility functions for setup scripts

# Get current user
CURRENT_USER=$(who am i | awk '{print $1}')
[ "$CURRENT_USER" = "" ] && CURRENT_USER=$(whoami)

# Default installation directory
INSTALL_DIR=${INSTALL_DIR:-"/home/$CURRENT_USER/zero-thermometer"}

# Check if script is running with sudo/root privileges
check_sudo() {
  if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
  fi
}

# Create a service file and symlink it
create_service() {
  local service_name=$1
  local service_content=$2
  
  # Create services directory if it doesn't exist
  mkdir -p "$INSTALL_DIR/services"
  
  # Create the service file
  echo "$service_content" > "$INSTALL_DIR/services/$service_name.service"
  
  # Create symlink
  ln -sf "$INSTALL_DIR/services/$service_name.service" "/etc/systemd/system/$service_name.service"
  
  # Reload systemd
  systemctl daemon-reload
  
  echo "Service $service_name created and symlinked"
}

# Enable and start a service
enable_service() {
  local service_name=$1
  
  systemctl enable "$service_name.service"
  systemctl restart "$service_name.service"
  echo "Service $service_name enabled and started"
}

# Read a value from .env file
read_env_var() {
  local var_name=$1
  local env_file="$INSTALL_DIR/.env"
  
  if [ -f "$env_file" ]; then
    local value=$(grep -E "^$var_name=" "$env_file" | cut -d '=' -f 2 | tr -d '"' | tr -d "'")
    echo "$value"
  else
    echo ""
  fi
}

# Ask for a value with a default
prompt_with_default() {
  local prompt=$1
  local default=$2
  local value
  
  read -p "$prompt [$default]: " value
  echo "${value:-$default}"
}

# Create directories with proper ownership
create_dir_with_owner() {
  local dir_path=$1
  local owner=$2
  
  mkdir -p "$dir_path"
  chown -R "$owner:$owner" "$dir_path"
}

# Detect Raspberry Pi model
detect_pi_model() {
  if [ -f /proc/device-tree/model ]; then
    cat /proc/device-tree/model | tr -d '\0'
  else
    echo "Unknown Raspberry Pi model"
  fi
}

# Check if we're running on a Raspberry Pi
is_raspberry_pi() {
  if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    return 0  # True
  else
    return 1  # False
  fi
}