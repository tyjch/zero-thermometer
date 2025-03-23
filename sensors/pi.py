import os
import psutil
import subprocess
import asyncio
from pint import Quantity
from .base import Sensor, Measurement, Measurable, units

class RaspberryPi(Sensor):
    """
    Sensor class for monitoring Raspberry Pi Zero system statistics
    """
    
    def __init__(self):
        super().__init__(
            name='RPi Zero 2W',
            preferred_units=[units.percent, units.fahrenheit, units.gigabyte]
        )
        # Get hardware-specific ID from Raspberry Pi serial number
        self._id = self._get_hardware_id()
        # Path to CPU temperature file
        self._temp_path = '/sys/class/thermal/thermal_zone0/temp'
        
    def _get_hardware_id(self):
        """Get a unique hardware ID from the Raspberry Pi serial number"""
        try:
            # Try to get the serial from /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        return line.split(':')[1].strip()[-8:]
                        
            # If that fails, try using the 'cat /proc/cpuinfo' command
            output = subprocess.check_output(
                "cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2", 
                shell=True
            ).decode('utf-8').strip()
            
            if output:
                return output[-8:]  # Last 8 characters of the serial
                
            # Last resort fallback
            return "pimonitor"
        except Exception as e:
            print(f"Error getting hardware ID: {e}")
            return "pimonitor"
    
    @property
    def id(self):
        return self._id
    
    @Measurable(frequency=5)
    async def cpu_load(self) -> Measurement:
        # Get CPU load as percentage (average over all cores)
        load = psutil.cpu_percent(interval=1)
        quantity = Quantity(load, units.percent)
        return self.create_measurement(quantity=quantity, override_dimension='cpu_load')
    
    @Measurable(frequency=5)
    async def memory_usage(self) -> Measurement:
        # Get memory usage as percentage
        memory = psutil.virtual_memory()
        quantity = Quantity(memory.percent, units.percent)
        return self.create_measurement(quantity=quantity, override_dimension='memory_usage')
    
    @Measurable(frequency=5)
    async def disk_usage(self) -> Measurement:
        # Get disk usage as percentage for root partition
        disk = psutil.disk_usage('/')
        quantity = Quantity(disk.percent, units.percent)
        return self.create_measurement(quantity=quantity, override_dimension='disk_usage')
    
    @Measurable(frequency=5)
    async def cpu_temp(self) -> Measurement:
        # Read CPU temperature from system file and convert to Fahrenheit
        try:
            with open(self._temp_path, 'r') as f:
                temp_millicelsius = int(f.read().strip())
                temp_celsius = temp_millicelsius / 1000.0
                # Create quantity in Celsius but will be converted to Fahrenheit by preferred_units
                quantity = Quantity(temp_celsius, units.celsius)
                return self.create_measurement(quantity=quantity)
        except (IOError, ValueError) as e:
            # Fallback for systems without temperature sensor
            print(f"Error reading CPU temperature: {e}")
            # Return 0°C as fallback (will be converted to °F)
            quantity = Quantity(0, units.celsius)
            return self.create_measurement(quantity=quantity)