# clients/influx.py
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from sensors.base import Measurement


class InfluxClient:

    def __init__(
        self,
        url            : str,
        token          : str,
        org            : str,
        bucket         : str,
        batch_size     : int = 10,
        flush_interval : int = 60
    ):
        self.url            = url
        self.token          = token
        self.org            = org
        self.bucket         = bucket
        self.batch_size     = batch_size
        self.flush_interval = flush_interval
        
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
        
        self.offline_buffer: List[Measurement] = []
        self.max_buffer_size = 10000
    
    async def send_measurement(self, measurement: Measurement) -> bool:
        try:
            point = self._create_point(measurement)
            self.write_api.write(bucket=self.bucket, record=point)
            return True
        except Exception as e:
            self.offline_buffer.append(measurement)
            self._manage_buffer()
            return False
    
    async def send_measurements(self, measurements: List[Measurement]) -> bool:
        try:
          points = [self._create_point(m) for m in measurements]
          self.write_api.write(bucket=self.bucket, record=points)
          return True
        except Exception as e:
          self.offline_buffer.extend(measurements)
          self._manage_buffer()
          return False
    
    def _create_point(self, measurement: Measurement) -> Point:
        point = Point("sensor_measurement")
        point = point.field("value", measurement.value)
        point = point.tag("sensor_id", measurement.sensor_id)
        point = point.tag("unit", measurement.unit)
        
        if measurement.metadata:
          for key, value in measurement.metadata.items():
            if isinstance(value, (str, int, float, bool)):
              point = point.tag(key, str(value))
        
        point = point.time(measurement.timestamp)
        
        return point
    
    async def retry_offline_data(self) -> int:
        if not self.offline_buffer:
          return 0
        
        current_buffer = self.offline_buffer.copy()
        self.offline_buffer = []
        
        sent_count = 0
        
        for i in range(0, len(current_buffer), self.batch_size):
          batch = current_buffer[i:i+self.batch_size]
          try:
              points = [self._create_point(m) for m in batch]
              self.write_api.write(bucket=self.bucket, record=points)
              sent_count += len(batch)
              await asyncio.sleep(0.1)  
          except Exception as e:
              self.offline_buffer.extend(batch)
              self._manage_buffer()
              break
        
        return sent_count
    
    def _manage_buffer(self) -> None:
        if len(self.offline_buffer) > self.max_buffer_size:
            excess = len(self.offline_buffer) - self.max_buffer_size
            self.offline_buffer = self.offline_buffer[excess:]
    
    def close(self) -> None:
        self.write_api.close()
        self.client.close()