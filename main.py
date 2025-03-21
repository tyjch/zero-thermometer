import os
import asyncio
from pprint import pprint
from dotenv import load_dotenv
from loguru import logger
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

async def main():
  temp_layer = TemperatureLayer()
  wifi_layer = WifiLayer()
  menu_layer = MenuLayer()
  screen     = Screen(layers=[temp_layer, wifi_layer])
  
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
  
  state = {'fahrenheit': 0.0, 'bias': 0.0}
  while True:
    measurements = await sampler.get_measurements()
    for m in measurements:
      if m.sensor_name == 'DS18B20':
        state['fahrenheit'] = m.value
        new_state = screen.refresh(state=state)
        if new_state:
          state = new_state
          logger.debug(f'State changed to: {state}')
      try:
        influx.insert_point(m)
      except Exception as e:
        logger.error(e)
        raise e
    #break

if __name__ == '__main__':
  asyncio.run(main())