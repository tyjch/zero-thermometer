from os import path
from .base import Layer
from PIL import Image, ImageDraw, ImageFont



class WifiLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=64)
    self.icons = {}
    self.load_icons()
    
  def load_icons(self):
    base_dir = path.dirname(path.abspath(__file__))
    icon_dir = path.join(base_dir, 'assets')
    for strength in range(5):
      icon_path = path.join(icon_dir, f'wifi_{strength}.png')
      if path.exists(icon_path):
        icon = Image.open(icon_path).convert('RGBA')
        self.icons[strength] = icon
  
  def update(self, image, data:dict):
    if self.visible and self.icons:
      icon = self.icons[self.strength]
      if icon:
        image.paste(icon, (0, 0), icon)
  
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
    elif quality < 0.3:
      return 1
    elif quality < 0.5:
      return 2
    elif quality < 0.7:
      return 3
    else:
      return 4
  
  
  
      
  