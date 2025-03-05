import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sensors.base import Sensor, Measurement


class Sampler:
  
    def __init__(
        self,
        sensors             : List[Sensor],
        sample_interval     : float = 60.0,
        samples_per_reading : int   = 1,
        sample_delay        : float = 0.5,
        averaging           : bool  = False
    ):
        self.sensors             = sensors
        self.sample_interval     = sample_interval
        self.samples_per_reading = samples_per_reading
        self.sample_delay        = sample_delay
        self.averaging           = averaging
        self.last_readings       = {}
        self.running             = False
        self.callback            = None
    
    def set_callback(self, callback):
        self.callback = callback
    
    def stop(self):
        self.running = False
    
    def update_config(self, config: Dict[str, Any]):
        if 'sample_interval' in config:
            self.sample_interval = config['sample_interval']
        if 'samples_per_reading' in config:
            self.samples_per_reading = config['samples_per_reading']
        if 'sample_delay' in config:
            self.sample_delay = config['sample_delay']
        if 'averaging' in config:
            self.averaging = config['averaging']
    
    async def sample_all(self) -> List[Measurement]:
        results = []
        
        for sensor in self.sensors:
            try:
                if self.averaging and self.samples_per_reading > 1:
                    measurement = await sensor.sample_average(
                        count=self.samples_per_reading,
                        interval=self.sample_delay
                    )
                elif self.samples_per_reading > 1:
                    measurements = await sensor.sample(
                        count=self.samples_per_reading,
                        interval=self.sample_delay
                    )
                    measurement = measurements[-1]  # Use the last measurement
                else:
                    measurement = await sensor.read()
                
                results.append(measurement)
                self.last_readings[sensor.id] = measurement
            except Exception as e:
                # Log error but continue with other sensors
                print(f"Error sampling sensor {sensor.id}: {e}")
        
        return results
    
    async def start_sampling_loop(self):
        self.running = True
        
        while self.running:
            measurements = await self.sample_all()
            
            if self.callback and measurements:
                await self.callback(measurements)
            
            await asyncio.sleep(self.sample_interval)
