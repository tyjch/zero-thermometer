# clients/influx.py
import os
import asyncio
from datetime import datetime
from dataclasses import asdict
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import WriteOptions
from sensors.base import Measurement
from .buffer import MeasurementBuffer
from loguru import logger


influx_log = logger.bind(tags=['influx'])


class InfluxClient:
  
  def __init__(
    self, 
    url             :str, 
    token           :str, 
    org             :str, 
    bucket          :str, 
    buffer          : MeasurementBuffer,
    batch_size      : int = 500,
    flush_interval  : int = 1_000,
    jitter_interval : int = 2_000,
    retry_interval  : int = 5_000  
  ):
    self.url    = url
    self.token  = token
    self.org    = org
    self.bucket = bucket
    self.buffer = buffer 
    
    if not all([self.url, self.token, self.org, self.bucket]):
      influx_log.critical('Missing InfluxDB environment variables')
      raise ValueError("Missing InfluxDB environment variables")
    
    self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
    influx_log.info(
      'Initialized InfluxDBClient', 
      url = self.url, 
      org = self.org
    )
    
    self.write_api = self.client.write_api(write_options=WriteOptions(
      batch_size      = batch_size,
      flush_interval  = flush_interval,
      jitter_interval = jitter_interval,
      retry_interval  = retry_interval
    ))
    influx_log.info(
      'Initialized InfluxDB WriteAPI', 
      batch_size      = batch_size, 
      flush_interval  = flush_interval,
      jitter_interval = jitter_interval,
      retry_interval  = retry_interval
    )
    
    
  def create_point(self, measurement:Measurement) -> Point:
    influx_log.trace('Creating point')
    
    data  = asdict(measurement)
    point = Point(measurement.sensor_name)
    
    if measurement.timestamp:
      point.time(int(measurement.timestamp.timestamp() * 1_000_000_000))
      
    for t in ['dimension', 'unit', 'sensor_id']:
      point.tag(t, getattr(measurement, t))
      
    point.field("value", measurement.value)
    
    return point
  
  def insert_measurement(self, measurement:Measurement):
    influx_log.trace('Inserting measurement')
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
    influx_log.trace('Inserting bias')
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
    influx_log.trace(
      'Processing buffer', 
      buffer_length = self.buffer.length
    )
    
    buffer_length = self.buffer.length
    buffer_measurements = self.buffer.get_pending(limit=limit)
    
    for i, m in buffer_measurements:
      try:
        point = self.create_point(m)
        self.write_api.write(bucket=self.bucket, record=point)
        self.buffer.mark_processed(i)
      except Exception as e:
        influx_log.error(f'Error processing buffered measurement: {e}')
        continue