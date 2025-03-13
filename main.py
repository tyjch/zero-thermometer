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
from clients.influx import InfluxClient
from clients.buffer import MeasurementBuffer
from display.screen import Screen

load_dotenv()

SHUTDOWN_PIN = board.D27
shutdown_button = None

# Shared state
latest_temperature = None

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

async def get_measurements(sensors):
  all_measurements = []
  for sensor in sensors:
    # Get all the async methods for this sensor
    methods = []
    for attr_name in dir(sensor):
      attr = getattr(sensor, attr_name)
      if callable(attr) and attr_name not in ('__init__', 'create_measurement') and not attr_name.startswith('_'):
        if asyncio.iscoroutinefunction(attr):
          methods.append(attr)
    
    # Call each method to get measurements
    for method in methods:
      try:
        measurement = await method()
        if measurement:
          all_measurements.append(measurement)
      except Exception as e:
        logger.error(f"Error getting measurement from {sensor.name}.{method.__name__}: {e}")
        
  return all_measurements

async def update_screen_task(screen):
    """Task to continuously update the screen without interruption"""
    global latest_temperature
    
    # Initial blank screen
    if screen:
        screen.show_value(None)
    
    while True:
        try:
            if screen and latest_temperature is not None:
                screen.show_value(latest_temperature)
            await asyncio.sleep(0.5)  # Update screen at 2Hz - adjust as needed
        except Exception as e:
            logger.error(f"Error updating screen: {e}")
            await asyncio.sleep(1)  # Wait a bit longer on error

async def measurement_task(sensors, influx, screen_task):
    """Task to collect and store measurements"""
    global latest_temperature
    
    while True:
        try:
            measurements = await get_measurements(sensors)
            
            for m in measurements:
                try:
                    is_successful = influx.insert_point(m)
                    if is_successful:
                        logger.success(f"Measurement inserted in InfluxDB: {m.dimension} from {m.sensor_name}")
                    else:
                        logger.warning(f"Measurement not inserted to InfluxDB: {m.dimension} from {m.sensor_name}")
                    
                    # Update the latest temperature if this is a DS18B20 temperature reading
                    if m.dimension == 'temperature' and m.sensor_name == 'DS18B20':
                        latest_temperature = m.value
                except Exception as e:
                    logger.error(f"Error processing measurement: {e}")
            
            # Process any buffered measurements
            influx.process_buffer(limit=20)
            
            # Wait before next reading cycle
            await asyncio.sleep(5)  # Read every 5 seconds
        except asyncio.CancelledError:
            logger.info("Measurement task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in measurement task: {e}")
            await asyncio.sleep(5)  # Wait a bit on error

async def main():
    global shutdown_button
    
    setup_shutdown_button()
    
    screen = Screen()
    buffer = MeasurementBuffer()
    influx = InfluxClient(
        url    = os.getenv('INFLUX_URL'),
        token  = os.getenv('INFLUX_TOKEN'),
        org    = os.getenv('INFLUX_ORG'),
        bucket = os.getenv('INFLUX_BUCKET'),
        buffer = buffer
    )
    
    sensors = [DS18B20(), SI7021(), RaspberryPi()]
    
    try:
        button_task  = asyncio.create_task(check_button())
        screen_task  = asyncio.create_task(update_screen_task(screen))
        measure_task = asyncio.create_task(measurement_task(sensors, influx, screen_task))
        await asyncio.gather(button_task, screen_task, measure_task)
    
    except Exception as e:
        logger.trace(f"Main loop error: {e}")
    finally:
        if shutdown_button:
            shutdown_button.deinit()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")