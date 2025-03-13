# clients/buffer.py
import os
import time
import json
import sqlite3
from dataclasses import asdict, is_dataclass
from typing import List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from sensors.base import Measurement

class MeasurementBuffer:
  
  def __init__(self, db_path='measurement_buffer.db', max_size=10000):
    self.type     = Measurement
    self.db_path  = db_path
    self.max_size = max_size
    
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    # Initialize the database
    self.initialize_db()
  
  def initialize_db(self):
    # Creates a table and index if either does not exist
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          CREATE TABLE IF NOT EXISTS measurements (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  REAL    NOT NULL,
            processed  INTEGER DEFAULT 0,
            data       TEXT    NOT NULL
          )            
        ''')
        
        cursor.execute('''
          CREATE INDEX IF NOT EXISTS idx_processed ON measurements(processed)
        ''')
        conn.commit()
    except Exception as e:
      print(f"Error initializing database: {e}")

  def serialize(self, measurement:Measurement):
    # Converts a Measurement into a string
    measurement_dict = asdict(measurement)
    for k, v in measurement_dict.items():
      if isinstance(v, datetime):
        measurement_dict[k] = v.isoformat()
    return json.dumps(measurement_dict)
  
  def deserialize(self, string:str):
    # Converts a string into a Measurement
    string_dict = json.loads(string)
    for k, v in string_dict.items():
      if k == 'timestamp' and isinstance(v, str):
        string_dict[k] = datetime.fromisoformat(v)
    return self.type(**string_dict)
  
  def insert(self, measurement):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          INSERT INTO measurements (timestamp, data, processed)
          VALUES (?, ?, 0)
        ''', (time.time(), self.serialize(measurement))
        )
        
        # Check if we need to rotate old processed records
        cursor.execute('SELECT COUNT(*) FROM measurements')
        count = cursor.fetchone()[0]
        if count > self.max_size:
          # Delete oldest processed records
          cursor.execute(
            'DELETE FROM measurements WHERE processed = 1 ORDER BY id ASC LIMIT ?', 
            (count - self.max_size,)
          )
        conn.commit()
        return True
    except Exception as e:
      print(f"Error inserting measurement: {e}")
      return False
  
  def get_pending(self, limit:int=100):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          SELECT id, data FROM measurements 
          WHERE processed = 0 
          ORDER BY id ASC LIMIT ?
        ''', (limit,)
        )
        results = []
        for row_id, data in cursor.fetchall():
          measurement = self.deserialize(data)
          results.append((row_id, measurement))
        return results
    except Exception as e:
      print(f"Error getting pending measurements: {e}")
      return []
  
  def mark_processed(self, measurement_id):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          UPDATE measurements 
          SET processed = 1
          WHERE id = ? 
        ''', (measurement_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
      print(f"Error marking measurement as processed: {e}")
      return False
  
  def delete_processed(self):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          DELETE FROM measurements 
          WHERE processed = 1
        ''')
        conn.commit()
        return cursor.rowcount
    except Exception as e:
      print(f"Error deleting processed measurements: {e}")
      return 0
    
  @property
  def length(self):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          SELECT COUNT(*) FROM measurements
          WHERE processed = 0 
        ''')
        return cursor.fetchone()[0]
    except Exception as e:
      print(f"Error getting buffer length: {e}")
      return 0