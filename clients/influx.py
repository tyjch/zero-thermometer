import os
import asyncio
from dataclasses import asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from sampler import Sample
from .buffer import SampleBuffer


class InfluxClient:
  
  def __init__(self, url:str, token:str, org:str, bucket:str, buffer:SampleBuffer):
    self.url    = url
    self.token  = token
    self.org    = org
    self.bucket = bucket
    self.buffer = buffer 
    
    if not all([self.url, self.token, self.org, self.bucket]):
      raise ValueError("Missing InfluxDB environment variables")
    
    
    self.client    = InfluxDBClient(url=self.url, token=self.token, org=self.org)
    self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
    
  def create_point(self, sample:Sample) -> Point:
    data  = asdict(sample)
    point = Point(sample.sensor_name)
    
    if sample.timestamp:
      point.time(int(sample.timestamp.timestamp() * 1_000_000_000))
    
    tags = ['dimension', 'unit', 'sensor_id']
    for t in tags:
      point.tag(t, getattr(sample, t))
    
    fields = ['mean', 'variance', 'minimum', 'maximum', 'sample_size', 'sample_delay']
    for f in fields:
      point.field(f, getattr(sample, f))
    
    timestamps = ['started', 'ended']
    for t in timestamps:
      point.field(t, getattr(sample, t).isoformat())
      
    return point
  
  def insert_point(self, sample):
    if self.write_api:
      try:
        point = self.create_point(sample)
        self.write_api.write(bucket=self.bucket, record=point)
        print("Wrote to Influx API")
        return True
      except Exception as e:
        print(e)
        self.buffer.insert(sample)
    else:
      self.buffer.insert(sample)
    
  def process_buffer(self, limit:int=100):
    buffer_length  = self.buffer.length
    buffer_samples = self.buffer.get_pending(limit=limit)
    
    for i, s in buffer_samples:
      try:
        point = self.create_point(s)
        self.write_api.write(bucket=self.bucket, record=point)
        self.buffer.mark_processed(i)
      except Exception as e:
        print(f'Error processinng buffered sample {sample_id}: {e}')
        break
    