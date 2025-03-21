import digitalio
from digitalio import DigitalInOut, Direction, Pull
from loguru import logger

class Button:
  
  def __init__(self, name:str, pin):
    self.name = name
    self.pin  = DigitalInOut(pin=pin)
    
    self.pin.direction = Direction.INPUT
    self.pin.pull      = Pull.UP
    
    self.callbacks = []
    self.running   = False
    self.task      = None
    
  def start(self):
    if self.task is None or self.task.done():
      self.task = asyncio.create_task(self.monitor())
  
  def stop(self):
    self.running = False
    if self.task is not None and not self.task.done():
      self.task.cancel()
      
  async def monitor(self):
    self.running = True
    last_state   = True
    
    while self.running:
      current_state = self.pin.value
      # Wait for debounce
      await asyncio.sleep(0.05)
      
      logger.debug(f'pin value: {self.pin.value}')
      if not self.pin.value:
        logger.debug(f'Button pressed: {self.name}')
        if self.callbacks:
          for c in self.callbacks:
            try:
              result = callback()
              if asyncio.iscoroutine(result):
                asyncio.create_task(result)
            except Exception as e:
              logger.error(f'Error in button callback: {e}')
              continue