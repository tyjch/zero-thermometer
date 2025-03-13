import asyncio
import statistics
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from loguru import logger
from sensors.base import Sensor, Measurement


class Sampler:
  
  def __init__(self, sensors:List[Sensor], dimensions:Optional[List[str]]=None):
    self.sensors       = sensors
    self.dimensions    = dimensions or ['temperature', 'relative_humidity']
    self.delay : float = 0.2
    
  async def get_measurements(self) -> List[Measurement]:
    measurements = []
    for sensor in self.sensors:
      for dimension, method in sensor.get_measurables().items():
        if dimension in self.dimensions:
          try:
            measurement = await method()
            if measurement is not None:
              measurements.append(measurement)
              await asyncio.sleep(self.delay)
          except Exception as e:
            logger.trace(f'Error getting measurement: {e}')
    return measurements
  