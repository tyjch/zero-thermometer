import asyncio
import board
import digitalio
from pprint import pprint
from typing import List, Optional
from dotenv import load_dotenv
from sensors.base import Sensor, Measurement
from sensors.ds18b20 import DS18B20
from sensors.si7021 import SI7021
from sampler import Sampler, Sample

print('Starting main.py')

load_dotenv()

    
async def main():
  s1, s2  = DS18B20(), SI7021()
  sampler = Sampler(sensors=[s1, s2])
  
  while True:
    samples = await sampler.get_samples()
    pprint(samples)
    break


if __name__ == '__main__':
  asyncio.run(main())