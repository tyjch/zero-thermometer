import os
import json
import asyncio
import statistics
import board
import digitalio
from datetime import datetime
from dataclasses import dataclass
from pprint import pprint
from typing import List, Optional
from dotenv import load_dotenv
from sensors.base import Sensor, Measurement
from sensors.ds18b20 import DS18B20
from sensors.si7021 import SI7021

print('Starting main.py')

load_dotenv()

@dataclass
class Sample:
  mean         : float
  variance     : float
  minimum      : float
  maximum      : float
  dimension    : str
  unit         : str
  sensor_name  : str
  sensor_id    : str
  sample_size  : int
  sample_delay : float
  timestamp    : datetime  # When the sample was created
  started      : datetime  # When the first measurement was made
  ended        : datetime  # When the last measurement was made

def condense(items:List, attribute:str):
  # Returns the value of an attribute if all items have the same value for that attribute
  unique_values = {getattr(i, attribute) for i in items}
  if len(unique_values) == 1:
    return unique_values.pop()
  else:
    raise ValueError("Not all values of the attribute are the same")

class Sampler:
  
  def __init__(self, sensors:List[Sensor], dimensions:Optional[List[str]]=None):
    self.sensors       = sensors
    self.dimensions    = dimensions or ['temperature', 'relative_humidity']
    self.size  : int   = 5
    self.delay : float = 0.5
    
  async def get_measurements(self, sensor_method) -> List[Measurement]:
    measurements = []
    for i in range(1, self.size):
      # TODO: Assumes the method is async
      m = await sensor_method()
      measurements.append(m)
      await asyncio.sleep(self.delay)
    return measurements
    
  def aggregate_measurements(self, measurements:List[Measurement]) -> Sample:
    values = [m.value for m in measurements]
    return Sample(
      mean         = statistics.mean(values),
      variance     = statistics.variance(values),
      minimum      = min(values),
      maximum      = max(values),
      unit         = condense(measurements, 'unit'),
      dimension    = condense(measurements, 'dimension'),
      sensor_name  = condense(measurements, 'sensor_name'),
      sensor_id    = condense(measurements, 'sensor_id'),
      sample_size  = self.size,
      sample_delay = self.delay,
      timestamp    = datetime.now(),
      started      = measurements[0].timestamp,
      ended        = measurements[-1].timestamp
    )

  async def get_samples(self) -> List[Sample]:
    samples = []
    for s in self.sensors:
      methods = [getattr(s, d, None) for d in self.dimensions]
      for m in methods:
        if m is not None and callable(m):
          measurements = await self.get_measurements(m)
          sample = self.aggregate_measurements(measurements)
          samples.append(sample)
    return samples
  
  
    
    
async def main():
  s1, s2  = DS18B20(), SI7021()
  sampler = Sampler(sensors=[s1, s2])
  
  while True:
    samples = await sampler.get_samples()
    pprint(samples)
    break


if __name__ == '__main__':
  asyncio.run(main())