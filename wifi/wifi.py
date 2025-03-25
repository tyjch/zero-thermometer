import subprocess
from datetime import datetime
from loguru import logger

wifi_log = logger.bind(tags=['wifi'])

class WifiManager:
  
  def __init__(self, scan_frequency=30):
    self.scan_frequency = scan_frequency
    self.last_scanned   = None
  
  def scan_networks(self):
    if self.last_scanned is not None:
      elapsed = time.time() - self.last_scanned
      if elapsed < self.scan_frequency:
        wifi_log.error('Skipped scanning networks')
        return
    else:
      subprocess.call("sudo nmcli device wifi rescan", shell=True, timeout=10)
      self.last_scanned = time.time()
  
  def connect(self, ssid):
    if ssid in self.connections:
      try:
        subprocess.call(
          f'sudo nmcli connection up {ssid}',
          shell=True
        )
      except Exception as e:
        wifi_log.error(f"Couldn't connect to {ssid}")
  
  def cycle_networks(self):
    current   = self.ssid
    available = list(self.available_connections.keys())
    if available:
      if len(available) == 1:
        wifi_log.info("No other network to cycle to")
      else:
        current_index = available.keys().index(current)
        try:
          next_ssid = available[current_index + 1]
          self.connect(next_ssid)
        except Exception as e:
          wifi_log.error(e)
    else:
      wifi_log.error("No networks to cycle to")   
  
  @property
  def networks(self):
    try:
      output = subprocess.check_output(
        "sudo nmcli -t -f SSID device wifi list", 
        shell = True
      ).decode('utf-8')
      lines = [line.strip() for line in output.splitlines()]
      return [ssid for ssid in lines if ssid != '--']
    except Exception:
      wifi_log.error('Failed to retrieve networks')
      return []
  
  @property
  def connections(self):
    keys = ['NAME', 'TYPE', 'STATE', 'ACTIVE', 'TIMESTAMP', 'AUTOCONNECT', 'AUTOCONNECT-PRIORITY']
    try:
      output = subprocess.check_output(
        f"sudo nmcli -t -f {','.join(keys)} connection show", 
        shell=True
      ).decode('utf-8')
      
      connections = {}
      for line in output.splitlines():
        values = line.split(':')
        row = {k:v for k, v in zip(keys, values)}
        connections[row['NAME']] = row
      return connections
    
    except Exception as e:
      wifi_log.error(f'Exception thrown: {e}')
      
  @property
  def available_connections(self):
    networks    = self.networks
    connections = self.connections.keys()
    return [c for c in connections if c in networks]
  
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
    
  
  
if __name__ == '__main__':
  wm = WifiManager()
  wifi_log.debug(wm.connections)
  wifi_log.debug(wm.networks)
  wifi_log.debug(wm.available_connections)