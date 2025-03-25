import asyncio
from os import path
import board
from .base import Layer
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
from gpiozero import Button, ButtonBoard

button_log = logger.bind(tag='button')

class MenuLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=20, anchor='rb', foreground=(150, 150, 150))
    self.active  = False
    self.icons   = {}
    self.load_icons()
    
    self.bias      = 0.0
    self.step_size = 0.1
    self.should_shutdown = False
    
    self.buttons = {
      'menu'  : Button(pin=27),
      'power' : Button(pin=17),
      'minus' : Button(pin=22),
      'plus'  : Button(pin=23)
    }
    
    self.buttons['menu'].when_activated  = self.toggle_menu
    self.buttons['power'].when_activated = self.shutdown
    self.buttons['minus'].when_activated = self.decrease_bias
    self.buttons['plus'].when_activated  = self.increase_bias
    
  
  def load_icons(self):
    base_dir = path.dirname(path.abspath(__file__))
    icon_dir = path.join(base_dir, 'assets')
    
    for name in ['close', 'menu', 'minus', 'plus', 'power']:
      icon_path = path.join(icon_dir, f'{name}.png')
      if path.exists(icon_path):
        icon = Image.open(icon_path).convert('RGBA')
        icon = self._resize_icon(icon, desired_height=32)
        
        pixel_data = icon.load()
        w, h = icon.size
        for y in range(h):
          for x in range(w):
            if pixel_data[x, y][3] > 0:
              pixel_data[x, y] = self.foreground + (pixel_data[x, y][3],)  # Preserve transparency

        self.icons[name] = icon
  
  def toggle_menu(self):
    button_log.info('Button pressed: (Menu)')
    self.active = not self.active
    logger.debug(f'Menu: {self.active}')
  
  def increase_bias(self):
    if self.active:
      button_log.info('Button pressed: (Plus)')
      self.bias += self.step_size
      self.bias = round(self.bias, 2)
    
  def decrease_bias(self):
    if self.active:
      button_log.info('Button pressed: (Minus)')
      self.bias -= self.step_size
      self.bias = round(self.bias, 2)
  
  def shutdown(self):
    if self.active:
      button_log.info('Button pressed: (Power)')
      for button in self.buttons.values():
        button.close()
      self.should_shutdown = True
      
  def update(self, image, state:dict):
    x, y = 280, 200
    if self.visible:
      if self.active:
        active_icons = ['close', 'plus', 'minus', 'power']
        draw = ImageDraw.Draw(image)
        draw.rectangle(
          (0, y, image.width, image.height),
          fill=(0, 0, 0)
        )
      else:
        active_icons = ['menu']
      
      for name in active_icons:
        icon = self.icons.get(name)
        if icon:
          image.paste(icon, (x, y), icon)
          x -= 91

    state['bias'] = self.bias
    if self.should_shutdown:
      button_log.info('Shutdown requested through shared state')
      state['shutdown'] = True
    return state
