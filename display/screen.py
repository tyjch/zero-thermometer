import time
import board
import digitalio
import adafruit_rgb_display.ili9341 as ili9341
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
from layers.temperature import TemperatureLayer
from pprint import pprint

class Screen:
  
  def __init__(self, layers, rotation:int=270):
    self.layers  = layers
    self.display = ili9341.ILI9341(
      board.SPI(),
      cs       = digitalio.DigitalInOut(board.CE0),
      dc       = digitalio.DigitalInOut(board.D25),
      rst      = digitalio.DigitalInOut(board.D24), 
      baudrate = 24000000,
      rotation = rotation
    )
  
    self.image = Image.new(
      "RGB", 
      (self.width, self.height), 
      (0, 0, 0)
    )
    
    self.draw = ImageDraw.Draw(self.image)
  
  def clear(self, fill_color=(0,0,0)):
    self.draw.rectangle(
      (0, 0, self.width, self.height),
      fill = fill_color
    )
  
  def show(self):
    try:
      self.image = self.image.rotate(angle=270.0) 
      self.display.image(self.image)
    except Exception as e:
      logger.error(f'Error in screen.show()')
      logger.debug(f'display: {self.display.width}x{self.display.height}')
      logger.debug(f'image: {self.image.width}x{self.image.height}')
      logger.debug(f'display rotation: {self.display.rotation}')
      #pprint(dir(self.draw))
      #pprint(dir(self.image))
      self.save()
      raise e
    
  def refresh(self, data):
    self.clear()
    for layer in self.layers:
      layer.update(self.draw, data=data)
    self.show()
  
  def save(self):
    self.image.save('my_screen.png')
  
  @property
  def width(self) -> int:
    # Get the current display width based on rotation
    return self.display.width
  
  @property
  def height(self) -> int:
    # Get the current display height based on rotation
    return self.display.height
  
  


if __name__ == '__main__':
  temp_layer = TemperatureLayer()
  s = Screen(layers=[temp_layer])
  
  d = {
    'fahrenheit' : 420.69
  }
  
  while True:
    try:
      s.refresh(data=d)
    except ValueError:
      break

    