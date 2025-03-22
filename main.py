import os
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

temp_layer = TemperatureLayer()
wifi_layer = WifiLayer()
menu_layer = MenuLayer()
screen     = Screen(layers=[wifi_layer, menu_layer, temp_layer])

buffer = MeasurementBuffer()
influx = InfluxClient(
  url    = os.getenv('INFLUX_URL'),
  token  = os.getenv('INFLUX_TOKEN'),
  org    = os.getenv('INFLUX_ORG'),
  bucket = os.getenv('INFLUX_BUCKET'),
  buffer = buffer
)

sampler = Sampler(
  sensors    = [DS18B20()], #, SHT41(), RaspberryPi()],
  dimensions = ['temperature', 'relative_humidity', 'cpu_load', 'cpu_temp']
)

async def main():
  state = {
    'fahrenheit' : 0.0, 
    'bias'       : 0.0
  }
  
  last_bias = 0.0
  
  while True:
    measurements = await sampler.get_measurements()
    for m in measurements:
      if m.sensor_name == 'DS18B20':
        state['fahrenheit'] = m.value
        
        new_state = screen.refresh(state=state)
        if new_state:
          state.update(new_state)
          logger.debug(f'State updated to: {state}')
      try:
        influx.insert_measurement(m)
        # Only log bias if it has changed
        current_bias = state['bias']
        if last_bias != current_bias:
          influx.insert_bias(current_bias, m)
          last_bias = current_bias
      except Exception as e:
        logger.error(e)
        raise e
    #break

if __name__ == '__main__':
  asyncio.run(main())
  
# Add atexit?
