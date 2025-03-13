import os
import asyncio
import board
import digitalio
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
from display.ili9341 import ILI9341

load_dotenv()

SHUTDOWN_PIN    = board.D27
shutdown_button = None

def setup_shutdown_button():
    global shutdown_button
    shutdown_button = digitalio.DigitalInOut(SHUTDOWN_PIN)
    shutdown_button.direction = digitalio.Direction.INPUT
    shutdown_button.pull = digitalio.Pull.UP
    logger.info(f"Shutdown button configured")

async def check_button():
    while True:
        if shutdown_button and not shutdown_button.value:  # Button is pressed (pulled LOW)
            logger.info("Shutdown button pressed. Shutting down...")
            os.system("sudo shutdown -h now")
        await asyncio.sleep(0.1)  # Check every 100ms

async def main():
  
  setup_shutdown_button()  
  
  display = ILI9341()
  buffer  = SampleBuffer()
  influx  = InfluxClient(
    url    = os.getenv('INFLUX_URL'),
    token  = os.getenv('INFLUX_TOKEN'),
    org    = os.getenv('INFLUX_ORG'),
    bucket = os.getenv('INFLUX_BUCKET'),
    buffer = buffer
  )
  
  s1 = DS18B20()
  s2 = SI7021()
  s3 = RaspberryPi()
  
  sampler = Sampler(
    sensors    = [s1, s2, s3],
    dimensions = ['temperature', 'relative_humidity', 'cpu_load', 'cpu_temp']
  )
  
  try:
    button_task = asyncio.create_task(check_button())
    while True:
        print('Awaiting samples')
        samples = await sampler.get_samples()
        for s in samples:
          try:
            influx.insert_point(s)
          except Exception as e:
            logger.error(e)
            raise e
        
        temperature_sample = next((s for s in samples if s.dimension == 'temperature'), None)
        if temperature_sample and display:
          display.show_value(temp_sample.mean)

  except Exception as e:
    logger.error(e)
  finally:
    if shutdown_button:
      shutdown_button.deinit()

if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    logger.info("Program terminated by user")