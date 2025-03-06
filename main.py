import os
import json
import board
import digitalio
from pprint import pprint
from dotenv import load_dotenv
from sensors.ds18b20 import DS18B20
from sensors.sht41 import SHT41
from sampler import Sampler

load_dotenv()

if __name__ == '__main__':
  core_sensor    = DS18B20()
  room_sensor    = SHT41()
  sensor_sampler = Sampler(sensors=[core_sensor])
  
  while True:
    measurements = sensor_sampler.sample_all()
    pprint(measurements)