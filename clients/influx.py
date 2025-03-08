import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from sampler import Sample

load_dotenv()

class SampleBuffer:
  def __init__(
    self, 
    buffer         : List[Dict],
    buffer_file    : 'sample_buffer.json',
    batch_size     : int,
    max_size       : 10000,
    flush_interval : int
  ):
    self.buffer_file = buffer_file
    pass


class InfluxClient:
  def __init__(self):
    self.url    = os.getenv('INFLUXDB_URL')
    self.token  = os.getenv('INFLUXDB_TOKEN')
    self.org    = os.getenv('INFLUXDB_ORG')
    self.bucket = os.getenv('INFLUXDB_BUCKET')
    
    if not all([self.url, self.token, self.org, self.bucket]):
      raise ValueError("Missing InfluxDB environment variables")
    
    self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
    self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
    
    
  

