import asyncio
from os import path
import board
import digitalio
from .base import Layer
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

class MenuLayer(Layer):
  
  def __init__(self):
    super().__init__(font_size=20, anchor='rb', foreground=(150, 150, 150))
    self.visible = False
    self.icons = {}
    self.bias = 0.0
    self.load_icons()
    
    # Button setup using DigitalIO
    self.buttons = {
      'menu': self._setup_button(board.D27),
      'power': self._setup_button(board.D17),
      'minus': self._setup_button(board.D22),
      'plus': self._setup_button(board.D23)
    }
  
  def _setup_button(self, pin):
    button = digitalio.DigitalInOut(pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    return {'pin': button, 'pressed': False, 'last_state': True}
  
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
  
  def _resize_icon(self, icon, desired_height=40):
    width, height = icon.size
    resized_width = int((desired_height/height)*width)
    resized_icon = icon.resize((resized_width, desired_height), Image.LANCZOS)
    return resized_icon
  
  def update(self, image, data:dict):
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
  
  async def monitor_buttons(self):
    while True:
      # Check menu button
      await self._check_button('menu', self._toggle_menu)
      
      # If menu is visible, check other buttons
      if self.visible:
        await self._check_button('power', self._power_action)
        await self._check_button('minus', self._decrease_bias)
        await self._check_button('plus', self._increase_bias)
      
      await asyncio.sleep(0.01)  # Small sleep to prevent CPU hogging
  
  async def _check_button(self, name, callback):
    button_info = self.buttons[name]
    current_state = button_info['pin'].value
    
    # Button is pressed when state is False (pulled low)
    if not current_state and button_info['last_state']:
      # Button just pressed
      button_info['pressed'] = True
      callback()
    elif current_state and not button_info['last_state']:
      # Button released
      button_info['pressed'] = False
    
    # Update last state
    button_info['last_state'] = current_state
  
  def _toggle_menu(self):
    self.visible = not self.visible
    logger.info(f"Menu {'visible' if self.visible else 'hidden'}")
  
  def _power_action(self):
    logger.info("Power button pressed")
    # Implement power action here
  
  def _increase_bias(self):
    self.bias += 0.1
    logger.info(f"Bias increased to {self.bias:.1f}")
  
  def _decrease_bias(self):
    self.bias -= 0.1
    logger.info(f"Bias decreased to {self.bias:.1f}")
    


