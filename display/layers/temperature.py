from .base import Layer
from PIL import Image, ImageDraw, ImageFont


class TemperatureLayer(Layer):
  
  def __init__(self):
    super().__init__()
    self.unit_symbol = "°F"
  
  def update(self, draw, data:dict):
    if 'fahrenheit' in data.keys():
      text = f'{data.get("fahrenheit", 0.0):.2f} {self.unit_symbol}'
      draw.text(
        (50, 50),
        text,
        font   = self.font,
        fill   = self.foreground,
        anchor = self.anchor
      )
  