# Validate GitHub token if available
if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_USERNAME" ] && [ -n "$GITHUB_REPO" ]; then
  echo "Validating GitHub token for $GITHUB_USERNAME/$GITHUB_REPO..."
  
  # Check if token works by making a simple API request
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${GITHUB_USERNAME}/${GITHUB_REPO}")
  
  if [ "$HTTP_STATUS" = "200" ]; then
    echo "GitHub token validation successful!"
  else
    echo "Warning: GitHub token validation failed (HTTP status: $HTTP_STATUS)."
    echo "Possible issues:"
    echo "- Token might be invalid or expired"
    echo "- Repository $GITHUB_USERNAME/$GITHUB_REPO might not exist"
    echo "- Token might not have 'repo' scope permissions"
    
    # Ask if user wants to continue
    read -p "Continue anyway? [y/N]: " continue_setup
    if [[ ! "$continue_setup" =~ ^[Yy]$ ]]; then
      echo "Setup aborted."
      exit 1
    fi
  fi
else
  echo "Warning: Missing GitHub credentials. Will prompt for them later."
fi#!/bin/bash
# install_github_runner.sh - Install and configure GitHub Actions Runner

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

echo "Setting up GitHub Actions Runner..."

# Get current user if not already set
CURRENT_USER=${CURRENT_USER:-$(whoami)}

# Create runner directory
RUNNER_DIR="/home/$CURRENT_USER/actions-runner"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Source .env file directly to get GitHub token
if [ -f "$INSTALL_DIR/.env" ]; then
  echo "Reading GitHub credentials from $INSTALL_DIR/.env file..."
  
  # Use grep and cut to extract the token value
  GITHUB_TOKEN=$(grep -E "^GITHUB_ACTIONS_TOKEN=" "$INSTALL_DIR/.env" | cut -d '=' -f 2 | tr -d '"' | tr -d "'")
  GITHUB_USERNAME=$(grep -E "^GITHUB_USERNAME=" "$INSTALL_DIR/.env" | cut -d '=' -f 2 | tr -d '"' | tr -d "'")
  GITHUB_REPO=$(grep -E "^GITHUB_REPO=" "$INSTALL_DIR/.env" | cut -d '=' -f 2 | tr -d '"' | tr -d "'")
else
  echo "Warning: .env file not found at $INSTALL_DIR/.env"
  GITHUB_TOKEN=""
  GITHUB_USERNAME=""
  GITHUB_REPO=""
fi

# Prompt for missing information
if [ -z "$GITHUB_TOKEN" ]; then
  echo "GITHUB_ACTIONS_TOKEN not found in .env file."
  GITHUB_TOKEN=$(prompt_with_default "Enter your GitHub Personal Access Token" "")
  if [ -z "$GITHUB_TOKEN" ]; then
    echo "GitHub token is required. Exiting."
    exit 1
  fi
fi

if [ -z "$GITHUB_USERNAME" ]; then
  GITHUB_USERNAME=$(prompt_with_default "Enter your GitHub username" "")
  if [ -z "$GITHUB_USERNAME" ]; then
    echo "GitHub username is required. Exiting."
    exit 1
  fi
fi

if [ -z "$GITHUB_REPO" ]; then
  GITHUB_REPO=$(prompt_with_default "Enter your repository name" "zero-thermometer")
  if [ -z "$GITHUB_REPO" ]; then
    echo "GitHub repository name is required. Exiting."
    exit 1
  fi
fi

# Get the latest runner version
echo "Fetching latest GitHub Actions Runner version..."
LATEST_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | jq -r '.tag_name[1:]')

# Download the runner package
echo "Downloading GitHub Actions Runner v${LATEST_VERSION}..."
curl -o actions-runner-linux-arm-${LATEST_VERSION}.tar.gz -L \
  https://github.com/actions/runner/releases/download/v${LATEST_VERSION}/actions-runner-linux-arm-${LATEST_VERSION}.tar.gz

# Extract the installer
echo "Extracting runner package..."
tar xzf ./actions-runner-linux-arm-${LATEST_VERSION}.tar.gz

# Get registration token
echo "Getting registration token..."
RUNNER_TOKEN=$(curl -s -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/${GITHUB_USERNAME}/${GITHUB_REPO}/actions/runners/registration-token | jq -r '.token')

if [ -z "$RUNNER_TOKEN" ] || [ "$RUNNER_TOKEN" = "null" ]; then
  echo "Failed to get runner token. Please check your GitHub token and repository information."
  exit 1
fi

# Configure the runner
echo "Configuring runner for ${GITHUB_USERNAME}/${GITHUB_REPO}..."
./config.sh --url https://github.com/${GITHUB_USERNAME}/${GITHUB_REPO} --token ${RUNNER_TOKEN} --unattended

# Make run.sh executable
chmod +x ./run.sh

# Create service file
SERVICE_CONTENT="[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
ExecStart=/home/$CURRENT_USER/actions-runner/run.sh
User=$CURRENT_USER
WorkingDirectory=/home/$CURRENT_USER/actions-runner
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=5min
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target"

# Create and enable service
check_sudo
create_service "github-actions-runner" "$SERVICE_CONTENT"
enable_service "github-actions-runner"

echo "GitHub Actions Runner installed and configured successfully."