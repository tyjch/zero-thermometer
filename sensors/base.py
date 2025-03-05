from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import uuid


@dataclass
class Measurement:
    value     : float
    unit      : str
    timestamp : datetime
    sensor_id : str
    metadata  : Optional[Dict[str, Any]] = None


class Sensor(ABC):
    
    def __init__(self, id: Optional[str]=None, name: Optional[str]=None):
        self.id = id if id else str(uuid.uuid4())
        self.name = name if name else self.__class__.__name__
        self.last_reading: Optional[Measurement] = None
    
    @abstractmethod
    async def read(self) -> Measurement:
        """Read a single measurement from the sensor"""
        pass
    
    async def sample(self, count: int=1, interval: float=0.5) -> List[Measurement]:
        """Take multiple samples from the sensor"""
        measurements = []
        for _ in range(count):
            measurement = await self.read()
            measurements.append(measurement)
            if _ < count - 1:  # Don't sleep after the last reading
                await asyncio.sleep(interval)
        
        self.last_reading = measurements[-1]  # Store the most recent reading
        return measurements

    async def sample_average(self, count: int=3, interval: float=0.5) -> Measurement:
        """Take multiple samples and return their average"""
        measurements = await self.sample(count, interval)
        
        # Calculate the average value
        avg_value = sum(m.value for m in measurements) / len(measurements)
        
        # Create a new measurement with the average value and current timestamp
        avg_measurement = Measurement(
            value=avg_value,
            unit=measurements[0].unit,  # Assume all measurements have the same unit
            timestamp=datetime.now(),
            sensor_id=self.id,
            metadata={"sample_count": count, "sample_interval": interval}
        )
        
        self.last_reading = avg_measurement
        return avg_measurement