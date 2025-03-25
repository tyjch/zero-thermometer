import os
import sys
import asyncio
from pprint import pprint
from dotenv import load_dotenv
from loguru import logger
from gpiozero import Device
from gpiozero.pins.lgpio import LGPIOFactory
from sensors.base import Sensor, Measurement
from sensors.ds18b20 import DS18B20
from sensors.sht41 import SHT41
from sensors.pi import RaspberryPi
from sampler import Sampler
from clients.influx import InfluxClient
from clients.buffer import MeasurementBuffer
from display.screen import Screen
from display.layers.temperature import TemperatureLayer
from display.layers.wifi import WifiLayer
from display.layers.menu import MenuLayer

      
load_dotenv()

def format_log(record):
  level    = record['level'].name
  time     = record['time']
  name     = record['name']
  function = record['function']
  line     = record['line']
  message  = record['message']
  tags     = record['extra'].get('tags', '')
  
  time_str     = f'<green>{time:YYYY-MM-DD HH:mm:ss}</green>'
  level_str    = f'<level>{level: <8}</level>'
  location_str = f'<cyan>{f"{name}.{function}:{line}": <40}</cyan>'
  message_str  = f'<level>{message}</level>'

  return f'\n{time_str} | {level_str} | {location_str} | {message_str}'

def filter_log(record, allowed_tags):
  record_tags = record['extra'].get('tags', [])
  return any(tag in record_tags for tag in allowed_tags)

logger.remove(0)
logger.add(
  sys.stderr, 
  colorize = True, 
  format   = format_log
)

temp_layer = TemperatureLayer()
wifi_layer = WifiLayer()
menu_layer = MenuLayer()

screen = Screen(layers=[
  wifi_layer, 
  menu_layer, 
  temp_layer
])

buffer = MeasurementBuffer()
influx = InfluxClient(
  url    = os.getenv('INFLUX_URL'),
  token  = os.getenv('INFLUX_TOKEN'),
  org    = os.getenv('INFLUX_ORG'),
  bucket = os.getenv('INFLUX_BUCKET'),
  buffer = buffer
)

sampler = Sampler(
  sensors    = [DS18B20(), SHT41(), RaspberryPi()],
  dimensions = ['temperature', 'relative_humidity', 'cpu_load', 'cpu_temp']
)


async def poll_sensors(state, sampler, influx, sleep_seconds=1):
  while True:
    measurements = await sampler.get_measurements()
    for m in measurements:
      if m.sensor_name == 'DS18B20':
        state['fahrenheit'] = m.value
      try:
        influx.insert_measurement(m)
        current_bias = state['bias']
        if state['last_bias'] != current_bias: 
          # Only send bias if it has changed
          influx.insert_bias(current_bias, m)
          state['last_bias'] = current_bias
      except Exception as e:
        logger.error(e)
        raise e
    await asyncio.sleep(sleep_seconds)

async def refresh_screen(state, screen, sleep_seconds=0.1):
  while True:
    new_state = screen.refresh(state=state)
    if new_state:
      state.update(new_state)
    await asyncio.sleep(sleep_seconds)
      
async def main():
  state = {
    'fahrenheit' : 0.0, 
    'bias'       : 0.0,
    'last_bias'  : 0.0,
    'shutdown'   : False
  }
  
  sensor_task = asyncio.create_task(poll_sensors(state, sampler, influx))
  screen_task = asyncio.create_task(refresh_screen(state, screen))
  
  await asyncio.gather(sensor_task, screen_task)
  

if __name__ == '__main__':
  asyncio.run(main())
  
# Add atexit?
