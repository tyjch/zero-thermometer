import subprocess
from os import path
from .base import Layer
from PIL import Image, ImageDraw, ImageFont
from loguru import logger


class WifiLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=20, anchor='lb', foreground=(150, 150, 150))
    self.icons = {}
    self.load_icons()
    
  def load_icons(self):
    base_dir = path.dirname(path.abspath(__file__))
    icon_dir = path.join(base_dir, 'assets')
    for strength in range(5):
      icon_path = path.join(icon_dir, f'wifi_{strength}.png')
      if path.exists(icon_path):
        icon = Image.open(icon_path).convert('RGBA')
        icon = self._resize_icon(icon)
        
        # Recolor the icon
        pixel_data = icon.load()
        w, h = icon.size
        for y in range(h):  # Fixed: use h directly, not icon.size[h]
          for x in range(w):  # Fixed: use w directly, not icon.size[w]
            if pixel_data[x, y][3] > 0:
              pixel_data[x, y] = self.foreground + (pixel_data[x, y][3],)  # Preserve transparency

        self.icons[strength] = icon  # Fixed: use icon instead of undefined recolored_icon
         
  def _resize_icon(self, icon, desired_height=40):
    width, height = icon.size
    resized_width = int((desired_height/height)*width)
    resized_icon = icon.resize((resized_width, desired_height), Image.LANCZOS)
    return resized_icon  # Fixed: add return statement
  
  def update(self, image, data:dict):
    if self.visible:
      strength = self.strength
      if strength in self.icons and self.icons[strength]:  # Fixed: check if key exists and icon is not None
        icon = self.icons[strength]
        image.paste(icon, (4, 0), icon)
        
      draw = ImageDraw.Draw(image)
      ssid = self.ssid
      ip_address = self.ip
      print(self.ip)
      
      if ssid:
        draw.text(
          (45, 29),
          ssid, 
          font   = self.font,
          fill   = self.foreground,
          anchor = 'lb' 
        )
        
      if ip_address:
        draw.text(
          (10, 220),
          ip_address,
          font   = self.font,
          fill   = self.foreground,
          anchor = 'lb'
        )   
  
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