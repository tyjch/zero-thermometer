import os
import asyncio
from pprint import pprint
from dotenv import load_dotenv
from loguru import logger
from sensors.base import Sensor, Measurement
from sensors.ds18b20 import DS18B20
from sensors.si7021 import SI7021
from sensors.pi import RaspberryPi
from sampler import Sampler
from clients.influx import InfluxClient
from clients.buffer import MeasurementBuffer
from display.screen import Screen

load_dotenv()

async def main():
  screen  = Screen()
  buffer  = MeasurementBuffer()
  influx  = InfluxClient(
    url    = os.getenv('INFLUX_URL'),
    token  = os.getenv('INFLUX_TOKEN'),
    org    = os.getenv('INFLUX_ORG'),
    bucket = os.getenv('INFLUX_BUCKET'),
    buffer = buffer
  )
  
  sampler = Sampler(
    sensors    = [DS18B20(), SI7021(), RaspberryPi()],
    dimensions = ['temperature', 'relative_humidity', 'cpu_load', 'cpu_temp']
  )
  
  while True:
    measurements = await sampler.get_measurements()
    for m in measurements:
      try:
        influx.insert_point(m)
      except Exception as e:
        logger.error(e)
        raise e

if __name__ == '__main__':
  asyncio.run(main())