import os
import time
import threading
import board
import digitalio
import adafruit_rgb_display.ili9341 as ili9341
from time import sleep
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from gpiozero import PWMLED, Device
from gpiozero.pins.lgpio import LGPIOFactory
from loguru import logger
from .layers.temperature import TemperatureLayer
from .layers.wifi import WifiLayer
from .layers.menu import MenuLayer


class Screen:
  
  def __init__(self, layers=None, rotation:int=270):
    self.active   = False
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
    
    # Initialize backlight with pin_factory set to prevent resets
    self.backlight = PWMLED(18)
    
    if rotation in (90, 270):
      img_width  = self.display.height
      img_height = self.display.width
    else:
      img_width  = self.display.width
      img_height = self.display.height
    
    self.image = Image.new(
      "RGB", 
      (img_width, img_height), 
      (0, 0, 0)
    )
    
    self.draw = ImageDraw.Draw(self.image)
    self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    
    self.startup()
    
  def clear(self, fill_color=(0, 0, 0)):
    self.draw.rectangle(
      (0, 0, self.image.width, self.image.height),
      fill = fill_color
    )
    
  def startup(self):
    self.clear()
    self.draw.text(
      (320//2, 240//2), 
      "Starting up...", 
      font   = self.font,
      anchor = 'mm',
      fill   = (150, 150, 150)
    )
    self.show()
    # Set backlight to full brightness
    self.set_backlight(1.0)
  
  def shutdown(self):
    # Turn off the backlight first
    self.set_backlight(0.0)
    
    # Show the shutdown message
    self.clear()
    self.draw.text(
      (320//2, 240//2), 
      "Shutting down...", 
      font   = self.font,
      anchor = 'mm',
      fill   = (150, 150, 150)
    )
    self.show()
    time.sleep(2)
    
    # Override the backlight close method to prevent cleanup
    original_close = self.backlight.close
    self.backlight.close = lambda: None
    
    # Create a direct hold on the pin to keep it in the off state
    try:
      # Get the underlying pin object
      pin = self.backlight._pin
      # Hold it low directly if possible
      if hasattr(pin, 'output') and callable(pin.output):
        pin.output(0)
    except Exception as e:
      print(f"Error holding pin: {e}")
    
    # Clear the screen
    self.clear()
    self.show()
    
    # Initiate shutdown
    os.system('sudo shutdown -h +15 "System will shut down in 15 seconds"')
    
  def show(self):
    try:
      # Don't rotate the image - the display already handles this
      self.display.image(self.image)
    except Exception as e:
      raise e
    
  def refresh(self, state):
    self.clear()
    if state.get('shutdown'):
      self.shutdown()
    else:
      for layer in self.layers:
        new_state = layer.update(self.image, state=state)
        if new_state:
          state = new_state
      self.show()
    return state
  
  def set_backlight(self, value:float):
    value = max(0.0, min(1.0, value))
    self.backlight.value = value
    
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