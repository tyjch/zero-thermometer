#!/bin/bash
# install_app.sh - Install Zero Thermometer application

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

# Determine if we're already in the repo
IN_REPO=false
if [ -f "$SCRIPT_DIR/../main.py" ]; then
  IN_REPO=true
  REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
  echo "Script is running from within a repository at $REPO_DIR"
fi

# Ask user if they want to use current directory or specify a different location
if [ "$IN_REPO" = true ]; then
  read -p "Install to current directory ($REPO_DIR)? [Y/n]: " use_current
  use_current=${use_current:-Y}
  
  if [[ "$use_current" =~ ^[Yy]$ ]]; then
    # Use the current repo directory
    INSTALL_DIR="$REPO_DIR"
    echo "Using current directory for installation"
  else
    # Prompt for custom location
    read -p "Enter installation directory [$INSTALL_DIR]: " custom_dir
    INSTALL_DIR=${custom_dir:-$INSTALL_DIR}
  fi
fi

# Create or update repository
if [ ! -d "$INSTALL_DIR" ]; then
  echo "Creating installation directory at $INSTALL_DIR..."
  mkdir -p "$INSTALL_DIR"
  
  # If we're in a repo, copy files; otherwise, clone
  if [ "$IN_REPO" = true ]; then
    echo "Copying repository files to $INSTALL_DIR..."
    cp -r "$REPO_DIR/." "$INSTALL_DIR"
  else
    echo "Cloning repository to $INSTALL_DIR..."
    REPO_URL=$(prompt_with_default "Enter the repository URL" "https://github.com/tyjch/zero-thermometer.git")
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi
else
  echo "Directory $INSTALL_DIR already exists."
  if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating existing repository..."
    cd "$INSTALL_DIR"
    git pull
  elif [ "$IN_REPO" = true ]; then
    echo "Copying repository files to $INSTALL_DIR..."
    cp -r "$REPO_DIR/." "$INSTALL_DIR"
  else
    echo "Directory exists but is not a git repository."
    echo "Will install into existing directory."
  fi
fi

# Create virtual environment and install dependencies
cd "$INSTALL_DIR"
echo "Setting up virtual environment..."

# Create venv directory with appropriate ownership
if [ "$EUID" -eq 0 ]; then
  # If running as root, ensure proper ownership
  create_dir_with_owner "$INSTALL_DIR/venv" "$CURRENT_USER"
else
  mkdir -p "$INSTALL_DIR/venv"
fi

python3 -m virtualenv venv
source venv/bin/activate

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
  echo "Installing Python dependencies..."
  pip install -r requirements.txt
else
  echo "Warning: requirements.txt not found. Manual installation of dependencies may be required."
fi

deactivate

# Ensure correct ownership of all files
if [ "$EUID" -eq 0 ]; then
  chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
fi

# Create .env file if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
  echo "Creating initial .env file from example..."
  if [ -f "$INSTALL_DIR/.env.example" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    echo "Please edit $INSTALL_DIR/.env with your actual configuration"
  else
    echo "Warning: .env.example not found, skipping .env creation"
  fi
fi

# Create the service file
# Get current user if not already set
CURRENT_USER=${CURRENT_USER:-$(whoami)}

SERVICE_CONTENT="[Unit]
Description=Zero Thermometer Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target"

# Create and enable service
check_sudo
create_service "zero-thermometer" "$SERVICE_CONTENT"
enable_service "zero-thermometer"

echo "Zero Thermometer application installed successfully."