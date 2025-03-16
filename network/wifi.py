#!/usr/bin/env python3
import os
import sys
import time
import yaml
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from loguru import logger

class WiFiManager:
  def __init__(self, config_path: str = "network/networks.yaml"):
    # Load configuration from YAML file
    self.config_path = config_path
    self.config = self.load_config()
    
    # Monitoring settings
    self.check_interval = self.config.get("check_interval", 300)  # Debug: Set to 5 seconds
    self.max_failures = self.config.get("max_failures", 3)
    self.ping_target = self.config.get("ping_target", "8.8.8.8")
    self.failure_count = 0
    self.current_network_index = 0
    
    # Determine the wireless interface name
    self.interface = self.get_wireless_interface()
    logger.info(f"Using wireless interface: {self.interface}")
    
    # Find current network index
    self.update_current_network_index()
  
  def get_wireless_interface(self) -> str:
    """Get the name of the wireless interface"""
    try:
      # Try using iwconfig to find wireless interfaces
      result = subprocess.run(
        ["iwconfig"], 
        capture_output=True, 
        text=True
      )
      
      # Parse output to find wireless interface names
      for line in result.stdout.split("\n"):
        if "IEEE 802.11" in line:
          interface = line.split()[0]
          return interface
      
      # Fallback to common interface names
      for interface in ["wlan0", "wlan1", "wifi0"]:
        result = subprocess.run(
          ["ifconfig", interface], 
          capture_output=True,
          text=True
        )
        if result.returncode == 0:
          return interface
      
      # Last resort fallback
      return "wlan0"
    except Exception as e:
      logger.error(f"Error detecting wireless interface: {e}")
      return "wlan0"
    
  def load_config(self) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
      config_file = Path(self.config_path)
      if not config_file.exists():
        # Create default config if it doesn't exist
        self.create_default_config()
      
      with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
      
      # Validate networks configuration
      if not config.get("networks"):
        raise ValueError("No networks defined in configuration")
      
      # Sort networks by priority (higher priority first)
      config["networks"] = sorted(
        config["networks"], 
        key=lambda x: x.get("priority", 0), 
        reverse=True
      )
      
      logger.info(f"Loaded {len(config['networks'])} networks from configuration")
      
      # Log network priorities for debugging
      for idx, network in enumerate(config["networks"]):
        logger.info(f"Network {idx}: {network['ssid']} (Priority: {network.get('priority', 0)})")
      
      return config
    
    except Exception as e:
      logger.error(f"Error loading configuration: {e}")
      # Return a default configuration
      return {
        "networks": [
          {
            "ssid": "DefaultNetwork",
            "priority": 10
          }
        ],
        "check_interval": 5,
        "max_failures": 3,
        "ping_target": "8.8.8.8"
      }
  
  def create_default_config(self):
    """Create a default configuration file"""
    try:
      config_dir = Path(self.config_path).parent
      config_dir.mkdir(parents=True, exist_ok=True)
      
      default_config = {
        "networks": [
          {
            "ssid": "PrimaryNetwork",
            "priority": 20,
            "description": "Home WiFi Network"
          },
          {
            "ssid": "BackupNetwork",
            "psk": "password",
            "priority": 10,
            "description": "iPhone Hotspot"
          }
        ],
        "check_interval": 5,
        "max_failures": 3,
        "ping_target": "8.8.8.8"
      }
      
      with open(self.config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
      
      logger.info(f"Created default configuration at {self.config_path}")
    
    except Exception as e:
      logger.error(f"Error creating default configuration: {e}")
  
  async def check_connection(self) -> bool:
    """Check if the current WiFi connection is working"""
    try:
      # Run ping with timeout
      process = await asyncio.create_subprocess_exec(
        'ping', '-c', '3', '-W', '5', self.ping_target,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
      )
      
      await process.wait()
      return process.returncode == 0
    except Exception as e:
      logger.error(f"Error checking connection: {e}")
      return False
  
  def get_current_ssid(self) -> Optional[str]:
    """Get the SSID of the currently connected network"""
    try:
      result = subprocess.run(
        ['iwgetid', '-r'], 
        capture_output=True, 
        text=True
      )
      if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
      
      # Alternative method using iw
      result = subprocess.run(
        ['iw', 'dev', self.interface, 'info'], 
        capture_output=True, 
        text=True
      )
      for line in result.stdout.split('\n'):
        if 'ssid' in line.lower():
          return line.split()[-1].strip()
      
      return None
    except Exception as e:
      logger.error(f"Error getting current SSID: {e}")
      return None
  
  def update_current_network_index(self) -> None:
    """Update the current network index based on the connected SSID"""
    current_ssid = self.get_current_ssid()
    if not current_ssid:
      logger.warning("Not connected to any network")
      return
      
    # Search through networks list to find the current SSID
    for i, network in enumerate(self.config["networks"]):
      if network["ssid"] == current_ssid:
        self.current_network_index = i
        logger.info(f"Currently connected to network index {i}: {current_ssid}")
        return
    
    logger.warning(f"Connected to network {current_ssid} which is not in the configuration")
  
  def create_wpa_config(self, network_index=None) -> str:
    """Create a wpa_supplicant.conf file with all configured networks
       Optionally prioritize a specific network by index"""
    config = [
      "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev",
      "update_config=1",
      "country=US",
      ""
    ]
    
    # If a specific network is specified, boost its priority
    boost_priority = 1000 if network_index is not None else 0
    
    for i, network in enumerate(self.config["networks"]):
      config.append("network={")
      config.append(f'    ssid="{network["ssid"]}"')
      if "psk" in network:
        config.append(f'    psk="{network["psk"]}"')
        
      # Apply extra priority boost to the specified network
      priority = network.get("priority", 0)
      if i == network_index:
        priority += boost_priority
        
      config.append(f'    priority={priority}')
      config.append("}")
      config.append("")
    
    return "\n".join(config)
  
  def force_connect_to_network(self, network_index: int) -> bool:
    """Force connection to a specific network by index"""
    try:
      network = self.config["networks"][network_index]
      logger.info(f"Forcing connection to network {network_index}: {network['ssid']}")
      
      # Create a wpa_supplicant.conf that heavily favors this network
      config_content = self.create_wpa_config(network_index)
      temp_config = Path("/tmp/wpa_supplicant.conf")
      temp_config.write_text(config_content)
      
      # Get full path for commands
      wpa_supplicant_path = "/etc/wpa_supplicant/wpa_supplicant.conf"
      
      # Copy to system location
      subprocess.run(['sudo', 'cp', str(temp_config), wpa_supplicant_path], check=True)
      subprocess.run(['sudo', 'chmod', '600', wpa_supplicant_path], check=True)
      
      # Try several different methods to apply new configuration
      
      # First method: Try wpa_cli disconnect/reconnect
      try:
        subprocess.run(['sudo', 'wpa_cli', '-i', self.interface, 'disconnect'], check=True)
        time.sleep(1)
        subprocess.run(['sudo', 'wpa_cli', '-i', self.interface, 'reconnect'], check=True)
      except:
        logger.warning("wpa_cli disconnect/reconnect failed")
      
      # Second method: Try restarting wpa_supplicant
      try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'], check=True)
        time.sleep(2)
      except:
        logger.warning("Restarting wpa_supplicant failed")
      
      # Third method: Try cycling interface
      try:
        subprocess.run(['sudo', 'ifconfig', self.interface, 'down'], check=True)
        time.sleep(1)
        subprocess.run(['sudo', 'ifconfig', self.interface, 'up'], check=True)
        time.sleep(3)
      except:
        logger.warning("Cycling interface failed")
      
      # Fourth method: Try explicit wpa_supplicant reload
      try:
        subprocess.run(['sudo', 'pkill', '-HUP', 'wpa_supplicant'], check=True)
        time.sleep(2)
      except:
        logger.warning("Sending HUP signal to wpa_supplicant failed")
      
      # Verify we're now connected to the right network
      time.sleep(3)  # Give it time to connect
      current_ssid = self.get_current_ssid()
      target_ssid = network["ssid"]
      
      # Check if we successfully connected
      if current_ssid == target_ssid:
        logger.info(f"Successfully connected to {target_ssid}")
        self.current_network_index = network_index
        return True
      else:
        logger.warning(f"Failed to connect to {target_ssid}, still on {current_ssid}")
        return False
    
    except Exception as e:
      logger.error(f"Error forcing connection to network: {e}")
      return False
  
  def switch_to_next_network(self) -> bool:
    """Switch to the next network in the priority list"""
    try:
      # Update current network index first
      self.update_current_network_index()
      
      # Move to next network
      next_index = (self.current_network_index + 1) % len(self.config["networks"])
      next_network = self.config["networks"][next_index]
      
      logger.info(f"Switching from network {self.current_network_index} ({self.get_current_ssid() or 'Unknown'}) to network {next_index}: {next_network['ssid']}")
      
      # Force connection to next network
      return self.force_connect_to_network(next_index)
      
    except Exception as e:
      logger.error(f"Error switching network: {e}")
      return False
  
  def switch_to_highest_priority(self) -> bool:
    """Switch to the highest priority network"""
    try:
      # Update current network index first
      self.update_current_network_index()
      
      # Only switch if we're not already on the highest priority network
      if self.current_network_index != 0:  # First network is highest priority
        highest_network = self.config["networks"][0]
        current_network = self.get_current_ssid() or "Unknown"
        
        logger.info(f"Switching from network {self.current_network_index} ({current_network}) to highest priority network: {highest_network['ssid']}")
        return self.force_connect_to_network(0)
      return True
    except Exception as e:
      logger.error(f"Error switching to highest priority network: {e}")
      return False
  
  async def monitor_connection(self):
    """Main loop to monitor WiFi connection and switch if needed"""
    logger.info("Starting WiFi connection monitoring")
    
    # Initial network configuration and index update
    self.update_current_network_index()
    current_ssid = self.get_current_ssid()
    
    if current_ssid:
      logger.info(f"Initially connected to: {current_ssid} (Index: {self.current_network_index})")
      
      # Check if we're not on the highest priority network
      if self.current_network_index != 0:
        logger.info(f"Not on highest priority network. Current: {current_ssid}, Highest: {self.config['networks'][0]['ssid']}")
        self.switch_to_highest_priority()
    
    while True:
      # Update current network index
      self.update_current_network_index()
      
      # Check current connection
      connection_ok = await self.check_connection()
      current_ssid = self.get_current_ssid()
      
      logger.info(f"Current connection status: {'OK' if connection_ok else 'Failed'}, Network: {current_ssid}, Index: {self.current_network_index}")
      
      if connection_ok:
        if self.failure_count > 0:
          logger.info(f"Connection restored to {current_ssid}")
        self.failure_count = 0
        
        # If we're not on the highest priority network, try to switch back
        if self.current_network_index != 0:
          logger.info(f"Not on highest priority network. Switching from {current_ssid} to {self.config['networks'][0]['ssid']}")
          self.switch_to_highest_priority()
      else:
        self.failure_count += 1
        logger.warning(f"Connection check failed ({self.failure_count}/{self.max_failures})")
        
        # Switch to next network if too many failures
        if self.failure_count >= self.max_failures:
          self.switch_to_next_network()
          self.failure_count = 0
      
      # Wait before next check
      await asyncio.sleep(self.check_interval)

async def main():
  # Configure logger
  logger.remove()
  # Add console logger
  logger.add(
    sys.stdout,
    level="INFO"
  )
  # Add file logger
  logger.add(
    "logs/wifi_manager.log",
    rotation="1 MB",
    retention="7 days",
    level="INFO"
  )
  
  # Create logs directory
  os.makedirs("logs", exist_ok=True)
  
  # Start manager
  manager = WiFiManager()
  try:
    await manager.monitor_connection()
  except Exception as e:
    logger.error(f"Error in main process: {e}", exc_info=True)

if __name__ == "__main__":
  asyncio.run(main())