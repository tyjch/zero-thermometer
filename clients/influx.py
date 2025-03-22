# clients/influx.py
import os
import asyncio
from datetime import datetime
from dataclasses import asdict
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from sensors.base import Measurement
from .buffer import MeasurementBuffer
from loguru import logger

class InfluxClient:
  
  def __init__(self, url:str, token:str, org:str, bucket:str, buffer:MeasurementBuffer):
    self.url    = url
    self.token  = token
    self.org    = org
    self.bucket = bucket
    self.buffer = buffer 
    
    if not all([self.url, self.token, self.org, self.bucket]):
      raise ValueError("Missing InfluxDB environment variables")
    
    self.client    = InfluxDBClient(url=self.url, token=self.token, org=self.org)
    self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
    
  def create_point(self, measurement:Measurement) -> Point:
    data  = asdict(measurement)
    point = Point(measurement.sensor_name)
    
    if measurement.timestamp:
      point.time(int(measurement.timestamp.timestamp() * 1_000_000_000))
    
    # Add tags for efficient querying
    tags = ['dimension', 'unit', 'sensor_id']
    for t in tags:
      point.tag(t, getattr(measurement, t))
    
    # Add the measurement value as a field
    point.field("value", measurement.value)
      
    return point
  
  def insert_measurement(self, measurement:Measurement):
    # TODO: Maybe only insert measurement if the value is different?
    if self.write_api:
      try:
        point = self.create_point(measurement)
        self.write_api.write(bucket=self.bucket, record=point)
        return True
      except Exception as e:
        print(e)
        self.buffer.insert(measurement)
    else:
      self.buffer.insert(measurement)
  
  def insert_bias(self, bias, measurement):
    point = Point('Bias')
    if measurement.timestamp:
      point.time(int(measurement.timestamp.timestamp() * 1_000_000_000))
    for t in ['dimension', 'unit', 'sensor_id']:
      point.tag(t, getattr(measurement, t))
    point.field("value", bias)
    
    if self.write_api:
      try:
        self.write_api.write(bucket=self.bucket, record=point)
        return True
      except Exception as e:
        logger.error(e)

  def process_buffer(self, limit:int=100):
    buffer_length = self.buffer.length
    buffer_measurements = self.buffer.get_pending(limit=limit)
    
    for i, m in buffer_measurements:
      try:
        point = self.create_point(m)
        self.write_api.write(bucket=self.bucket, record=point)
        self.buffer.mark_processed(i)
      except Exception as e:
        print(f'Error processing buffered measurement {i}: {e}')
        break