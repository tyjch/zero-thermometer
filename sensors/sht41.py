import board
import adafruit_sht4x
from loguru import logger
from pint import Quantity
from .base import Sensor, Measurement, Measurable, units

class SHT41(Sensor):
  
  def __init__(self):
    super().__init__(name='SHT41', preferred_units=[units.fahrenheit, units.percent])
    self._sensor = adafruit_sht4x.SHT4x(board.I2C())

  @property
  def id(self):
    return self._sensor.serial_number
  
  @Measurable(frequency=30)
  async def temperature(self) -> Measurement:
    quantity = Quantity(self._sensor.temperature, units.celsius)
    return self.create_measurement(quantity=quantity)
    
  @Measurable(frequency=30)
  async def relative_humidity(self) -> Measurement:
    try:
      quantity = Quantity(self._sensor.relative_humidity, units.percent)
      return self.create_measurement(quantity=quantity, override_dimension='relative_humidity')
    except ValueError as e:
      logger.error(e)
      pass
    
    
