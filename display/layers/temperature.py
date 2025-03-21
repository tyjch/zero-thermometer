from .base import Layer
from enum import Enum
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

class TemperatureStatus(Enum):
  INACTIVE = 0
  COLD     = 1
  COOL     = 2
  AVERAGE  = 3
  WARM     = 4
  HOT      = 5
  
temperature_ranges = {
  TemperatureStatus.INACTIVE : {
    'max'   : 95.0, 
    'color' : (150, 150, 150)
  },
  TemperatureStatus.COLD     : {
    'max'   : 96.5, 
    'color' : (50, 120, 220)
  },
  TemperatureStatus.COOL     : {
    'max'   : 97.0, 
    'color' : (130, 180, 255)
  },
  TemperatureStatus.AVERAGE  : {
    'max'   : 98.0, 
    'color' : (255, 255, 255)
  },
  TemperatureStatus.WARM     : {
    'max'   : 99.0, 
    'color' : (255, 170, 130)
  },
  TemperatureStatus.HOT      : {
    'max'   : float('inf'), 
    'color' : (255, 130, 90)
  }
}

class TemperatureLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=8*10)
    self.unit_symbol = "°F"
  
  def get_temperature_status(self, value) -> TemperatureStatus:
    temperature_status = TemperatureStatus.INACTIVE
    for status, d in temperature_ranges.items():
      maximum_value = d['max']
      if value >= maximum_value:
        continue
      else:
        temperature_status = status
        break
    #logger.debug(f'value: {value:.2f}, state: {temperature_status}')
    return temperature_status
  
  def update(self, image, state:dict) -> None:
    draw = ImageDraw.Draw(image)
    if 'fahrenheit' in state.keys():
      value  = state.get("fahrenheit", 0.0)
      status = self.get_temperature_status(value)
      color  = temperature_ranges[status]['color']
      text   = f'{state.get("fahrenheit", 0.0):.1f}{self.unit_symbol}'
      draw.text(
        (320//2, 240//2),
        text,
        font   = self.font,
        fill   = color or self.foreground,
        anchor = self.anchor
      )