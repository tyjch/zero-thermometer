from gpiozero import Button as GPIOButton
from typing import Callable, List
from loguru import logger

class Button:
  def __init__(self, pin: int, name: str, bounce_time: float = 0.05):
    """
    Initialize a button with interrupt-based detection using gpiozero.
    
    Args:
        pin: GPIO pin number (BCM numbering)
        name: Name identifier for the button
        bounce_time: Debounce time in seconds (default 0.05s = 50ms)
    """
    self.name = name
    self.button = GPIOButton(
      pin=pin, 
      pull_up=True,
      bounce_time=bounce_time
    )
    
    # Keep track of callbacks
    self.callbacks = []
    
    # Set up the event handler
    self.button.when_pressed = self._handle_press
  
  def add_callback(self, callback: Callable) -> None:
    """Add a callback to be called when the button is pressed"""
    self.callbacks.append(callback)
  
  def _handle_press(self):
    """Handler called when the button is pressed"""
    logger.debug(f"Button {self.name} pressed")
    
    # Call all registered callbacks
    for callback in self.callbacks:
      try:
        callback()
      except Exception as e:
        logger.error(f"Error in button callback: {e}")
  
  def close(self):
    """Close the button and free associated resources"""
    self.button.close()