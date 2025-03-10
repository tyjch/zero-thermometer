import os
import asyncio
from pprint import pprint
from dotenv import load_dotenv
from loguru import logger
from sensors.base import Sensor, Measurement
from sensors.ds18b20 import DS18B20
from sensors.si7021 import SI7021
from sensors.pi import RaspberryPi
from sampler import Sampler, Sample
from clients.influx import InfluxClient
from clients.buffer import SampleBuffer

load_dotenv()

async def main():
  buffer = SampleBuffer()
  influx = InfluxClient(
    url    = os.getenv('INFLUX_URL'),
    token  = os.getenv('INFLUX_TOKEN'),
    org    = os.getenv('INFLUX_ORG'),
    bucket = os.getenv('INFLUX_BUCKET'),
    buffer = buffer
  )
  
  s1 = DS18B20()
  s2 = SI7021()
  #s3 = RaspberryPi()
  
  sampler = Sampler(
    sensors    = [s1, s2],
    dimensions = [
      'temperature',
      'relative_humidity'
      # 'cpu_load',
      # 'memory_usage',
      # 'disk_usage',
    ]
    )
  
  while True:
    print('Awaiting samples')
    samples = await sampler.get_samples()
    for s in samples:
      try:
        is_successful = influx.insert_point(s)
        if is_successful:
          logger.success("Point inserted in InfluxDB")
        else:
          logger.warning("Point not inserted to InfluxDB")
      except Exception as e:
        logger.error(e)
        raise e

if __name__ == '__main__':
  asyncio.run(main())