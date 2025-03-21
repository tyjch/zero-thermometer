import asyncio
from os import path
import board
import digitalio
from .base import Layer
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
from ..button import Button

class MenuLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=20, anchor='rb', foreground=(150, 150, 150))
    self.visible = False
    self.icons   = {}
    self.load_icons()
    
    self.buttons = {
      'menu'  : Button(name='menu',  pin=27),
      'power' : Button(name='power', pin=17),
      'minus' : Button(name='minus', pin=22),
      'plus'  : Button(name='plus',  pin=23)
    }
    
    for b in self.buttons.values():
      b.add_callback(lambda n: logger.debug(n))
    
    
  def load_icons(self):
    base_dir = path.dirname(path.abspath(__file__))
    icon_dir = path.join(base_dir, 'assets')
    
    for name in ['menu', 'minus', 'plus', 'power']:
      icon_path = path.join(icon_dir, f'{name}.png')
      if path.exists(icon_path):
        icon = Image.open(icon_path).convert('RGBA')
        icon = self._resize_icon(icon)
        
        pixel_data = icon.load()
        w, h = icon.size
        for y in range(h):
          for x in range(w):
            if pixel_data[x, y][3] > 0:
              pixel_data[x, y] = self.foreground + (pixel_data[x, y][3],)  # Preserve transparency

        self.icons[name] = icon
  
  def update(self, image, state:dict):
    if self.visible:
      # Display the menu icons across the bottom of the screen
      if 'menu' in self.icons:
        icon = self.icons['menu']
        image.paste(icon, (10, 240 - icon.height - 10), icon)
      
      if 'minus' in self.icons:
        icon = self.icons['minus']
        image.paste(icon, (90, 240 - icon.height - 10), icon)
      
      if 'plus' in self.icons:
        icon = self.icons['plus']
        image.paste(icon, (170, 240 - icon.height - 10), icon)
      
      if 'power' in self.icons:
        icon = self.icons['power']
        image.paste(icon, (250, 240 - icon.height - 10), icon)
      
      # Display bias value
      draw = ImageDraw.Draw(image)
      draw.text(
        (160, 140),
        f"Bias: {self.bias:.1f}",
        font=self.font,
        fill=self.foreground,
        anchor='mm'
      )
  
 


