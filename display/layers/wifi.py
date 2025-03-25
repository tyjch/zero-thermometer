import subprocess
from os import path
from .base import Layer
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

wifi_log = logger.bind(tags=['wifi'])

class WifiLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=20, anchor='lb', foreground=(150, 150, 150))
    self.icons = {}
    self.load_icons()
    self.connection_index = 0
    
  def load_icons(self):
    base_dir = path.dirname(path.abspath(__file__))
    icon_dir = path.join(base_dir, 'assets')
    
    for strength in range(5):
      icon_path = path.join(icon_dir, f'wifi_{strength}.png')
      
      if path.exists(icon_path):
        icon = Image.open(icon_path).convert('RGBA')
        icon = self.resize_icon(icon, desired_height=40)
        icon = self.recolor_icon(icon, desired_color=self.foreground)
        self.icons[strength] = icon 
  
  def update(self, image, state:dict):
    if self.visible:
      strength = self.strength
      if strength in self.icons and self.icons[strength]:
        icon = self.icons[strength]
        image.paste(icon, (4, 0), icon)
      draw = ImageDraw.Draw(image)
      
      ssid = self.ssid
      if ssid:
        draw.text(
          (45, 29),
          ssid, 
          font   = self.font,
          fill   = self.foreground,
          anchor = 'lb' 
        )
        #logger.debug(f'ssid color: {self.foreground}')
      
      ip_address = self.ip
      if ip_address:
        draw.text(
          (10, 220),
          ip_address,
          font   = self.font,
          fill   = self.foreground,
          anchor = 'lb'
        )
        #logger.debug(f'ip color: {self.foreground}')
      
      #available_networks = self.available_networks
      #wifi_log.debug(f'{available_networks}')
      available_connections = self.available_connections
      wifi_log.debug(f'{available_connections}')
  
  @property
  def quality(self):
    try:
      output = subprocess.check_output(
        "iwconfig wlan0 | grep -i quality", 
        shell=True
      ).decode('utf-8')
      
      # Parse the output to get signal quality
      quality_parts = output.split('=')[1].split('/')
      quality = int(quality_parts[0]) / int(quality_parts[1].split(' ')[0])
      return quality
    except Exception as e:
      return 0
  
  @property
  def strength(self):
    q = self.quality
    if q == 0:
      return 0
    elif q < 0.3:
      return 1
    elif q < 0.5:
      return 2
    elif q < 0.7:
      return 3
    else:
      return 4
  
  @property
  def ssid(self):
    try:
      output = subprocess.check_output(
        "iwconfig wlan0 | grep -i essid", 
        shell=True
      ).decode('utf-8')
      
      ssid_part = output.split('ESSID:')[1].strip()
      if ssid_part.startswith('"') and ssid_part.endswith('"'):
        ssid_part = ssid_part[1:-1]
      
      return ssid_part
    except Exception as e:
      return "Not connected"
  
  @property
  def ip(self):
    try:
      output = subprocess.check_output(
        "hostname -I | awk '{print $1}'", 
        shell=True
      ).decode('utf-8').strip()
      
      if output:
        return output
      return "No IP"
    except Exception as e:
      return "No IP"
  
  def rescan_networks(self):
    try:
      subprocess.call("sudo nmcli device wifi rescan", shell=True, timeout=10)
      wifi_log.success('Network scan successful with `sudo nmcli`')
    except subprocess.TimeoutExpired:
      wifi_log.error('Timed out')
    except Exception:
      wifi_log.error('Network scan failed with `sudo nmcli`')
      try:
        subprocess.call(
          "nmcli device wifi rescan", 
          shell   = True, 
          timeout = 10
        )
        wifi_log.success('Network scan successful with `nmcli`')
      except Exception:
        wifi_log.error('Network scan failed with `nmcli`')
  
  @property
  def networks(self):
    self.rescan_networks()
    # Try to get results using sudo
    try:
      try:
        output = subprocess.check_output(
          "sudo nmcli -t -f SSID device wifi list", 
          shell = True
        ).decode('utf-8')
      except Exception:
        wifi_log.error('Network listing failed with `sudo nmcli`')
        output = subprocess.check_output(
          "nmcli -t -f SSID device wifi list", 
          shell=True
        ).decode('utf-8')
      
      networks = []
      for line in output.splitlines():
        ssid = line.strip()
        if ssid and ssid not in networks and ssid != "--":
          networks.append(ssid)
      
      return networks
    
    except Exception as e:
      wifi_log.error("Network listing failed: falling back to `iwlist`")
      try:
        output = subprocess.check_output(
          "sudo iwlist wlan0 scan | grep -i essid", 
          shell=True
        ).decode('utf-8')
        networks = []
        for line in output.splitlines():
          if "ESSID:" in line:
            ssid = line.split('ESSID:"')[1].strip('"')
            if ssid and ssid not in networks:
              networks.append(ssid)
        return networks
      except Exception:
        return []
  
  @property
  def connections(self):
    try:
      output = subprocess.check_output(
        "sudo nmcli -t -f NAME,TYPE,AUTOCONNECT,AUTOCONNECT-PRIORITY connection show", 
        shell=True
      ).decode('utf-8')
      
      connections = {}
      for line in output.splitlines():
        if not line.strip():
          continue
          
        parts = line.strip().split(':')
        if len(parts) >= 4 and parts[1] == '802-11-wireless':  # Only get WiFi connections
          name = parts[0]
          autoconnect = parts[2].lower() == 'yes'
          try:
            priority = int(parts[3])
          except (ValueError, IndexError):
            priority = 0
            
          # Get the SSID for this connection
          try:
            ssid_output = subprocess.check_output(
              f"sudo nmcli -t -f 802-11-wireless.ssid connection show '{name}'", 
              shell=True
            ).decode('utf-8').strip()
            
            if ssid_output and ':' in ssid_output:
              ssid = ssid_output.split(':', 1)[1].strip()
              
              connections[ssid] = {
                'name': name,
                'autoconnect': autoconnect,
                'priority': priority
              }
          except Exception:
            # Skip connections where we can't get the SSID
            pass
            
      return connections
    except Exception as e:
      return {}
  
  @property
  def available_connections(self):
    networks    = self.networks
    connections = self.connections.keys()
    return [c for c in connections if c in networks]
