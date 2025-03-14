from .base import Layer
from PIL import Image, ImageDraw, ImageFont


class TemperatureLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=64)
    self.unit_symbol = "°F"
  
  def update(self, draw, data:dict):
    if 'fahrenheit' in data.keys():
      text = f'{data.get("fahrenheit", 0.0):.1f} {self.unit_symbol}'
      draw.text(
        (320//2, 240//2),
        text,
        font   = self.font,
        fill   = self.foreground,
        anchor = self.anchor
      )
      
  