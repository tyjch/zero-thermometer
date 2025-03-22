from gpiozero import LED, Button
from signal import pause
from loguru import logger

button = Button(27)

def log():
  logger.debug('Hello world!')

button.when_pressed = log

try:
  logger.info("Press the button (Pin 27) to see debug messages. Press Ctrl+C to exit.")
  pause()
except KeyboardInterrupt:
  logger.info("Exiting...")
  button.close()