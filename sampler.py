import sys
import asyncio
import statistics
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from loguru import logger
from sensors.base import Sensor, Measurement

sampler_log = logger.bind(tag='sampler')

class Sampler:
  
  def __init__(self, sensors:List[Sensor], dimensions:Optional[List[str]]=None):
    self.sensors    = sensors
    self.dimensions = dimensions or ['temperature', 'relative_humidity']
    self.delay      = 0.2

  async def get_measurements(self) -> List[Measurement]:
    measurements = []
    for sensor in self.sensors:
      for dimension, method in sensor.get_measurables().items():
        if dimension in self.dimensions:
          with sampler_log.contextualize(sensor=sensor, dimension=dimension):
            try:
              sampler_log.trace('Awaiting result of sensor method')
              measurement = await method()
              if measurement is not None:
                measurements.append(measurement)
                sampler_log.trace('Measurement added to sample')
                await asyncio.sleep(self.delay)
            except Exception as e:
              sampler_log.error(f'Error occured while taking sensor reading: {e}')
    return measurements
