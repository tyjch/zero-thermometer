from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont

class Layer(ABC):
  def __init__(
    self,
    foreground = (255, 255, 255),
    background = (0, 0, 0),
    font_path  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    font_size  = 32,
    anchor     = 'mm'
  ):
    self.foreground = foreground
    self.background = background
    self.font_size  = font_size
    self.anchor     = anchor
    self.visible    = True
    
    try:
      self.font = ImageFont.truetype(font_path, font_size)
    except IOError:
      self.font = ImageFont.load_default()
  
  @abstractmethod
  def update(self, image, state:dict):
    pass
  
  def recolor_icon(self, icon, desired_color):
    pixel_data = icon.load()
    w, h = icon.size
    for y in range(h):
      for x in range(w):
        if pixel_data[x, y][3] > 0:
          pixel_data[x, y] = desired_color + (pixel_data[x, y][3],)  # Preserve transparency
    return icon
  
  def resize_icon(self, icon, desired_height):
    width, height = icon.size
    resized_width = int((desired_height/height)*width)
    resized_icon = icon.resize((resized_width, desired_height), Image.LANCZOS)
    return resized_icon
  