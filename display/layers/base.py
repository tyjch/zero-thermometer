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
  
  # @abstractmethod
  # def update(display, data:dict):
  #   pass
  
  