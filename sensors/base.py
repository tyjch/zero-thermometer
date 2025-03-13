import os
import glob
import time
import asyncio
import inspect
import board
import adafruit_si7021
import RPi.GPIO as GPIO
from functools import wraps
from loguru import logger
from pint import UnitRegistry, Unit, Quantity
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable


units = UnitRegistry()
units.formatter.default_format = '.2f'


@dataclass
class Measurement:
  value       : float
  dimension   : str
  unit        : str
  sensor_name : str
  sensor_id   : str
  timestamp   : datetime


class Measurable:
  def __init__(self, frequency:int=5):
    self.frequency      = frequency
    self.dimension      = None
    self._last_measured = None
    
  def __call__(self, method):
    @wraps(method)
    async def wrapper(sensor_instance, *args, **kwargs):
      # TODO: Do I check if self.dimension is none and then update or just do it this way?
      self.dimension = self.dimension or method.__name__
      now = datetime.now()
      
      if self.ready:
        result = await method(sensor_instance, *args, **kwargs)
        self.last_measured = now
        return result
      
      return None
    
    wrapper.measurable = self
    return wrapper
      
  @property
  def ready(self) -> bool:
    if self.last_measured is None:
      return True
    else:
      now = datetime.now()
      # TODO: Do I check self.last_measured or self._last_measured?
      seconds_elapsed = (now - self.last_measured).total_seconds()
      return seconds_elapsed >= self.frequency
    
  @property
  def last_measured(self) -> Optional[datetime]:
    return self._last_measured
    
  @last_measured.setter
  def last_measured(self, value:datetime) -> None:
    self._last_measured = value
      

class Sensor(ABC):
    
  def __init__(self, name:str, preferred_units:Optional[List[Unit]]=[]):
    self.name            : str        = name
    self.preferred_units : List[Unit] = preferred_units or []
    
  @property
  @abstractmethod
  def id(self):
    pass

  def get_measurables(self):
    measurables = {}
    for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
      if hasattr(method, 'measurable'):
        if method.measurable.ready:
          measurables[name] = method
    return measurables

  def create_measurement(self, quantity:Quantity, override_dimension:Optional[str]=None):
    logger.debug('Creating measurement')
    quantity   = quantity.to_preferred(self.preferred_units)
    dimensions = list(quantity.dimensionality.keys())
    
    if not dimensions:
      if override_dimension:
        dimension = override_dimension
      else:
        raise ValueError("Must provide an override_dimension for dimensionless quantities")
    elif len(dimensions) == 1:
      dimension = dimensions[0].strip('[]')
    else:
      raise ValueError("Compound dimensions are not supported")
    
    return Measurement(
      value       = quantity.magnitude,
      dimension   = dimension,
      unit        = str(quantity.units).lower(),
      sensor_name = self.name,
      sensor_id   = self.id,
      timestamp   = datetime.now()
    )
