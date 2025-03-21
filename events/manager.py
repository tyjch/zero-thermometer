import subprocess
import RPi.GPIO as GPIO
from loguru import logger

class EventManager:
  
  def __init__(self):
    self.buttons : {
      'menu'  : board.D27,
      'power' : board.D17,
      'minus' : board.D22,
      'plus'  : board.D23
    }
    self.initialize_gpio()
    
  def initialize_gpio(self):
    for name, pin in self.buttons.items():
      button = digitalio.DigitalInOut(pin)
      button.direction = digitalio.Direction.INPUT
      button.pull      = digitalio.Pull.UP
      self.buttons[name] = button
      
      
  def callback(self, channel):
    logger.debug(f'Button pressed, channel: {channel}')
    
  
  def shutdown(self):
    pass
  

if __name__ == '__main__':
  em = EventManager()
  