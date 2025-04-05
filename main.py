import os
import sys
import asyncio
from dotenv import load_dotenv
from loguru import logger
from gpiozero import Device, PWMLED
from gpiozero.pins.lgpio import LGPIOFactory
from sensors import Sensor, Measurement, DS18B20, SHT41, RaspberryPi
from sampler import Sampler
from clients import InfluxClient, MeasurementBuffer
from display import Screen
from display.layers import TemperatureLayer, WifiLayer, MenuLayer

load_dotenv()

#region Logger
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

logger.remove(0)
logger.add(sys.stderr, colorize=True, format=format_log)
#endregion

#region Screen 
screen = Screen()
temp_layer = TemperatureLayer()
wifi_layer = WifiLayer()
menu_layer = MenuLayer()

screen.layers = [
  temp_layer, 
  wifi_layer, 
  menu_layer
]
#endregion

#region Measurements 

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
#endregion


async def poll_sensors(state, sleep_seconds=1):
  buffer  = MeasurementBuffer()
  influx  = InfluxClient(
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
  while True:
    measurements = await sampler.get_measurements()
    for m in measurements:
      if m.sensor_name == 'DS18B20':
        state['fahrenheit'] = m.value
      try:
        influx.insert_measurement(m)
        current_bias = state['bias']
        if state['last_bias'] != current_bias: 
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
    'shutdown'   : False,
    'location'   : 'main'
  }
  
  sensor_task = asyncio.create_task(poll_sensors(state))
  screen_task = asyncio.create_task(refresh_screen(state, screen))
  
  # Create a task to watch for shutdown
  async def shutdown_monitor():
    while True:
      if state.get('shutdown'):
        # Cancel all other tasks
        sensor_task.cancel()
        screen_task.cancel()
        return
      await asyncio.sleep(0.1)
  
  monitor_task = asyncio.create_task(shutdown_monitor())
  
  try:
    await asyncio.gather(sensor_task, screen_task, monitor_task)
  except asyncio.CancelledError:
    # Handle task cancellation
    pass
  
  # Ensure screen shows shutdown message
  screen.shutdown()


if __name__ == '__main__':
  fan = PWMLED(19)
  fan.value = 1.0
  asyncio.run(main())