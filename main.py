import os
import asyncio
from pprint import pprint
from dotenv import load_dotenv
from loguru import logger
from sensors.base import Sensor, Measurement
from sensors.ds18b20 import DS18B20
from sensors.si7021 import SI7021
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
    buffer = buffer,
  )
  
  s1, s2  = DS18B20(), SI7021()
  sampler = Sampler(sensors=[s1, s2])
  
  while True:
    print('Awaiting samples')
    samples = await sampler.get_samples()
    for s in samples:
      try:
        influx.insert_point(s)
        logger.success("Point inserted in InfluxDB")
      except Exception as e:
        logger.error(e)
        raise e

if __name__ == '__main__':
  asyncio.run(main())