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
  
  def __init__(self, layers=None, rotation:int=270):
    self.layers   = layers or []
    self.rotation = rotation
    self.display  = ili9341.ILI9341(
      board.SPI(),
      cs       = digitalio.DigitalInOut(board.CE0),
      dc       = digitalio.DigitalInOut(board.D25),
      rst      = digitalio.DigitalInOut(board.D24), 
      baudrate = 24000000,
      rotation = rotation
    )
    
    # When rotation is 90 or 270, we need to swap width and height for the image
    if rotation in (90, 270):
      img_width  = self.display.height
      img_height = self.display.width
    else:
      img_width  = self.display.width
      img_height = self.display.height
    
    # Create image with the correct dimensions based on rotation
    self.image = Image.new(
      "RGB", 
      (img_width, img_height), 
      (0, 0, 0)
    )
    
    self.draw = ImageDraw.Draw(self.image)
    
    # Log the dimensions for debugging
    logger.debug(f"Display dimensions: {self.display.width}x{self.display.height}")
    logger.debug(f"Image dimensions: {self.image.width}x{self.image.height}")
  
  def clear(self, fill_color=(0,0,0)):
    self.draw.rectangle(
      (0, 0, self.image.width, self.image.height),
      fill = fill_color
    )
    
    # Upper Bar
    self.draw.rectangle(
      (0, 0, 320, 60),
      fill = (255, 0, 0)
    )
    # Temperature
    self.draw.rectangle(
      (0, 60, 320, 180),
      fill = (0, 0, 0)
    )
    # Lower Bar
    self.draw.rectangle(
      (0, 240-60, 320, 240),
      fill = (0, 0, 255),
    )
  
  def show(self):
    try:
      # Don't rotate the image - the display already handles this
      self.display.image(self.image)
    except Exception as e:
      logger.error(f'Error in screen.show(): {e}')
      logger.debug(f'display: {self.display.width}x{self.display.height}')
      logger.debug(f'image: {self.image.width}x{self.image.height}')
      logger.debug(f'display rotation: {self.display.rotation}')
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
    # For drawing purposes, use the image width
    return self.image.width
  
  @property
  def height(self) -> int:
    # For drawing purposes, use the image height
    return self.image.height
  


if __name__ == '__main__':
  temp_layer = TemperatureLayer()
  s = Screen(layers=[temp_layer])
  
  d = {
    'fahrenheit' : 97.5
  }
  
  try:
    s.refresh(data=d)
    time.sleep(1)  
  except Exception as e:
    logger.error(f"Error in main: {e}")