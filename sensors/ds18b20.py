import glob
import board
from pint import Quantity
from .base import Sensor, Measurement, units


class DS18B20(Sensor):
  
  def __init__(self):
    # TODO: Handle multiple DS18B20 devices
    super().__init__(name='DS18B20', preferred_units=[units.fahrenheit])
    self._base_dir = '/sys/bus/w1/devices/'
    self._folder   = glob.glob(self._base_dir + '28*')[0]
    self._file     = self._folder + '/w1_slave'
    self._id       = self._folder.split('/')[-1]

  @property
  def id(self):
    return self._id
  
  async def temperature(self) -> Measurement:
    quantity = Quantity(await self._temperature(), units.celsius)
    return self.create_measurement(quantity=quantity)
    
  async def _temperature(self):
    def read_file():
      try:
        with open(self._file, 'r') as f:
          lines = f.readlines()
        return lines
      except Exception as e:
        raise RuntimeWarning(f"Error reading sensor file: {e}")
        return None
   
    lines = read_file()
    if not lines:
      return None
    
    while lines[0].strip()[-3:] != 'YES':
      time.sleep(0.2)
      lines = read_file()
    
    equals_position = lines[1].find('t=')
    if equals_position != -1:
      temperature_string  = lines[1][equals_position+2:]
      temperature_celsius = float(temperature_string) / 1000.0
      return temperature_celsius
        
    