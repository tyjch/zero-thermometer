# clients/influx.py
import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from sensors.base import Measurement
from dotenv import load_dotenv



class InfluxClient:

    def __init__(
        self,
        buffer_file    : Optional[str] = "offline_buffer.json",
        batch_size     : int = 10,
        flush_interval : int = 60
    ):
        load_dotenv()

        self.url            = os.getenv('INFLUXDB_URL')
        self.token          = os.getenv('INFLUXDB_TOKEN')
        self.org            = os.getenv('INFLUXDB_ORG')
        self.bucket         = os.getenv('INFLUXDB_BUCKET')

        self.batch_size     = batch_size
        self.flush_interval = flush_interval
        self.buffer_file    = buffer_file

        if not all([self.url, self.token, self.org, self.bucket]):
            raise ValueError("Missing required InfluxDB configuration. Provide parameters or set environment variables.")

        self.client    = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)

        self.offline_buffer: List[Dict] = []
        self.max_buffer_size = 10000

        self._load_buffer_from_file()

    async def send_measurement(self, measurement: Measurement) -> bool:
        try:
            point = self._create_point(measurement)
            self.write_api.write(bucket=self.bucket, record=point)
            return True
        except Exception as e:
            # Store in memory buffer and file
            self.offline_buffer.append(self._measurement_to_dict(measurement))
            self._manage_buffer()
            self._save_buffer_to_file()
            return False

    async def send_measurements(self, measurements: List[Measurement]) -> bool:
        try:
            points = [self._create_point(m) for m in measurements]
            self.write_api.write(bucket=self.bucket, record=points)
            return True
        except Exception as e:
            # Store in memory buffer and file
            for m in measurements:
                self.offline_buffer.append(self._measurement_to_dict(m))
            self._manage_buffer()
            self._save_buffer_to_file()
            return False

    async def retry_offline_data(self, sleep_duration=0.1) -> int:
        if not self.offline_buffer:
            return 0

        current_buffer = self.offline_buffer.copy()
        self.offline_buffer = []

        sent_count = 0

        for i in range(0, len(current_buffer), self.batch_size):
            batch = current_buffer[i:i+self.batch_size]

            try:
                measurements = [self._dict_to_measurement(item) for item in batch]
                points       = [self._create_point(m) for m in measurements]

                self.write_api.write(
                    bucket = self.bucket,
                    record = points
                )

                sent_count += len(batch)
                await asyncio.sleep(sleep_duration)

            except Exception as e:
                self.offline_buffer.extend(batch)
                self._manage_buffer()
                self._save_buffer_to_file()
                break

        if sent_count > 0:
            self._save_buffer_to_file()

        return sent_count

    def close(self) -> None:
        try:
            self._save_buffer_to_file()
            if self.write_api:
                self.write_api.close()
            if self.client:
                self.client.close()
        except Exception as e:
            print(f"Error closing InfluxDB client: {e}")

    # region Magic Methods
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()
    # endregion
    
    # region Converters
    def _measurement_to_dict(self, measurement: Measurement) -> Dict:
        return {
            "value"     : measurement.value,
            "unit"      : measurement.unit,
            "timestamp" : measurement.timestamp.isoformat(),
            "sensor_id" : measurement.sensor_id,
            "metadata"  : measurement.metadata or {}
        }

    def _dict_to_measurement(self, data: Dict) -> Measurement:
        return Measurement(
            value     = data["value"],
            unit      = data["unit"],
            timestamp = datetime.fromisoformat(data["timestamp"]),
            sensor_id = data["sensor_id"],
            metadata  = data["metadata"]
        )
    # endregion
    
    # region Buffer Methods
    def _save_buffer_to_file(self) -> None:
        if not self.buffer_file:
            return
        else:
            try:
                with open(self.buffer_file, 'w') as f:
                    json.dump(self.offline_buffer, f)
            except Exception as e:
                print(f"Error saving buffer to file: {e}")

    def _load_buffer_from_file(self) -> None:
        if not self.buffer_file or not os.path.exists(self.buffer_file):
            return
        try:
            with open(self.buffer_file, 'r') as f:
                self.offline_buffer = json.load(f)

        except Exception as e:
            print(f"Error loading buffer from file: {e}")
            self.offline_buffer = []
    
    def _manage_buffer(self) -> None:
        if len(self.offline_buffer) > self.max_buffer_size:
            excess = len(self.offline_buffer) - self.max_buffer_size
            self.offline_buffer = self.offline_buffer[excess:]
            self._save_buffer_to_file()
    # endregion


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

    

