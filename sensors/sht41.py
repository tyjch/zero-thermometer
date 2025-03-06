import time
import board
import adafruit_sht4x
from datetime import datetime
from typing import Optional, Literal, Dict, Any
from .base import Sensor, Measurement


class SHT41(Sensor):

    def __init__(
        self, 
        id               : Optional[str] = None, 
        name             : Optional[str] = None,
        measurement_type : Literal["temperature", "humidity"] = "temperature",
        i2c_address      : int = 0x44
    ):
        super().__init__(id, name)
        self.measurement_type = measurement_type
        self.i2c              = board.I2C()
        self.sensor           = adafruit_sht4x.SHT4x(self.i2c)
        self.sensor.mode      = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
        self.units = {
            "temperature" : "°C",
            "humidity"    : "%RH"
        }
    
    async def read(self) -> Measurement:
        try:
            temperature, relative_humidity = self.sensor.measurements
            
            value = temperature if self.measurement_type == "temperature" else relative_humidity
            unit  = self.units[self.measurement_type]
            
            measurement = Measurement(
                value     = value,
                unit      = unit,
                timestamp = datetime.now(),
                sensor_id = self.id,
                metadata  = {
                    "sensor_type"      : "SHT41",
                    "measurement_type" : self.measurement_type,
                    "all_readings"     : {
                        "temperature" : temperature,
                        "humidity"    : relative_humidity
                    }
                }
            )
            
            self.last_reading = measurement
            return measurement
            
        except Exception as e:
            # In a real application, you might want to log this error
            raise RuntimeError(f"Error reading from SHT41: {e}")