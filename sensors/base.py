import os
import glob
import time
import asyncio
import functools
import board
import adafruit_si7021
import RPi.GPIO as GPIO
from pint import UnitRegistry, Unit, Quantity
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from pprint import pprint


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


class Sensor(ABC):
    
  def __init__(self, name:str, preferred_units:Optional[List[Unit]]=[]):
    self.name            : str        = name
    self.preferred_units : List[Unit] = preferred_units or []
    
  @property
  @abstractmethod
  def id(self):
    # Should return an id unique to the hardware
    pass

  def create_measurement(self, quantity:Quantity, override_dimension:Optional[str]=None):
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
