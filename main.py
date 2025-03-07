import os
import json
import board
import digitalio
from pprint import pprint
from dotenv import load_dotenv
from sensors.ds18b20 import DS18B20
from sensors.si7021 import SI7021

load_dotenv()

def collect_measurements(sensors, dimensions=['temperature', 'relative_humidity']):
  measurements = []
  
  for s in sensors:
    methods = [getattr(s, d, None) for d in dimensions]
    
    for m in methods:
      if m is not None and callable(m):
        measurement = m()
        measurements.append(measurement)
        
  return measurements

if __name__ == '__main__':
  s1, s2  = DS18B20(), SI7021()
  sensors = [s1, s2]  
  
  while True:
    measurements = collect_measurements(sensors=sensors)
    pprint(measurements)
    break