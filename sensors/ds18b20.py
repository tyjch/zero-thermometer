import os
import glob
from datetime import datetime
import asyncio
from typing import Optional, List
from .base import Sensor, Measurement


class DS18B20Sensor(Sensor):

    def __init__(self, id: Optional[str] = None, name: Optional[str] = None):
        super().__init__(id, name)
        self.base_dir = '/sys/bus/w1/devices/'
        self.device_folder = self._find_device()
        if not self.device_folder:
            raise RuntimeError("DS18B20 sensor not found")
        
        self.device_file = os.path.join(self.device_folder, 'temperature')
    
    def _find_device(self) -> Optional[str]:
        try:
            device_folders = glob.glob(os.path.join(self.base_dir, '28-*'))
            if device_folders:
                return device_folders[0]
            return None
        except Exception as e:
            raise RuntimeError(f"Error finding DS18B20 device: {e}")
    
    async def _read_temp_raw(self) -> Optional[str]:
        try:
            with open(self.device_file, 'r') as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Error reading from DS18B20: {e}")
    
    async def read(self) -> Measurement:
        try:
            temp_string = await self._read_temp_raw()
            if temp_string:
                temp_c = float(temp_string) / 1000.0
                measurement = Measurement(
                    value     = temp_c,
                    unit      = "°C",
                    timestamp = datetime.now(),
                    sensor_id = self.id,
                    metadata  = {
                        "sensor_type" : "DS18B20",
                        "raw_reading" : temp_string
                    }
                )
                
                self.last_reading = measurement
                return measurement
            
            raise RuntimeError("Unable to read temperature from DS18B20")
            
        except Exception as e:
            raise RuntimeError(f"Error processing DS18B20 reading: {e}")