from .base import Layer
from enum import Enum
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

class TemperatureState(Enum):
  INACTIVE = 0
  COLD     = 1
  COOL     = 2
  AVERAGE  = 3
  WARM     = 4
  HOT      = 5
  
temperature_ranges = {
  TemperatureState.INACTIVE : {
    'max'   : 95.0, 
    'color' : (150, 150, 150)
  },
  TemperatureState.COLD     : {
    'max'   : 96.5, 
    'color' : (50, 120, 220)
  },
  TemperatureState.COOL     : {
    'max'   : 97.0, 
    'color' : (130, 180, 255)
  },
  TemperatureState.AVERAGE  : {
    'max'   : 98.0, 
    'color' : (255, 255, 255)
  },
  TemperatureState.WARM     : {
    'max'   : 99.0, 
    'color' : (255, 170, 130)
  },
  TemperatureState.HOT      : {
    'max'   : float('inf'), 
    'color' : (255, 130, 90)
  }
}

class TemperatureLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=8*10)
    self.unit_symbol = "°F"
  
  def get_temperature_state(self, value):
    temperature_state = TemperatureState.INACTIVE
    for state, d in temperature_ranges.items():
      maximum_value = d['max']
      if value >= maximum_value:
        continue
      else:
        temperature_state = state
        break
    logger.debug(f'value: {value}, state: {temperature_state}')
    return temperature_state
  
  def update(self, image, data:dict):
    draw = ImageDraw.Draw(image)
    if 'fahrenheit' in data.keys():
      value = data.get("fahrenheit", 0.0)
      state = self.get_temperature_state(value)
      color = temperature_ranges[state]['color']
      text = f'{data.get("fahrenheit", 0.0):.1f}{self.unit_symbol}'
      draw.text(
        (320//2, 240//2),
        text,
        font   = self.font,
        fill   = color or self.foreground,
        anchor = self.anchor
      )
      

  