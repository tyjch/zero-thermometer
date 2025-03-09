import os
import time
import json
import sqlite3
from dataclasses import asdict, is_dataclass
from typing import List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from sampler import Sample

class SampleBuffer:
  
  def __init__(self, db_path='sample_buffer.db', max_size=10000):
    self.type     = Sample
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
          CREATE TABLE IF NOT EXISTS samples (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  REAL    NOT NULL,
            processed  INTEGER DEFAULT 0,
            data       TEXT    NOT NULL
          )            
        ''')
        
        cursor.execute('''
          CREATE INDEX IF NOT EXISTS idx_processed ON samples(processed)
        ''')
        conn.commit()
    except Exception as e:
      print(f"Error initializing database: {e}")

  def serialize(self, sample:Sample):
    # Converts a Sample into a string
    sample_dict = asdict(sample)
    for k, v in sample_dict.items():
      if isinstance(v, datetime):
        sample_dict[k] = v.isoformat()
    return json.dumps(sample_dict)  # Return the JSON string
  
  def deserialize(self, string:str):
    # Converts a string into a Sample
    string_dict = json.loads(string)
    for k, v in string_dict.items():
      if k in ('timestamp', 'started', 'ended') and isinstance(v, str):
        string_dict[k] = datetime.fromisoformat(v)
    return self.type(**string_dict)
  
  def insert(self, sample):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          INSERT INTO samples (timestamp, data, processed)
          VALUES (?, ?, 0)
        ''', (time.time(), self.serialize(sample))
        )
        
        # Check if we need to rotate old processed records
        cursor.execute('SELECT COUNT(*) FROM samples')
        count = cursor.fetchone()[0]
        if count > self.max_size:
          # Delete oldest processed records
          cursor.execute(
            'DELETE FROM samples WHERE processed = 1 ORDER BY id ASC LIMIT ?', 
            (count - self.max_size,)
          )
        conn.commit()
        return True
    except Exception as e:
      print(f"Error inserting sample: {e}")
      return False
  
  def get_pending(self, sample_limit:int=100):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          SELECT id, data FROM samples 
          WHERE processed = 0 
          ORDER BY id ASC LIMIT ?
        ''', (sample_limit,)  # Fixed parameter name
        )
        results = []
        for row_id, data in cursor.fetchall():
          sample = self.deserialize(data)
          results.append((row_id, sample))
        return results
    except Exception as e:
      print(f"Error getting pending samples: {e}")
      return []
  
  def mark_processed(self, sample_id):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          UPDATE samples 
          SET processed = 1
          WHERE id = ? 
        ''', (sample_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
      print(f"Error marking sample as processed: {e}")
      return False
  
  def delete_processed(self):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          DELETE FROM samples 
          WHERE processed = 1
        ''')
        conn.commit()
        return cursor.rowcount
    except Exception as e:
      print(f"Error deleting processed samples: {e}")
      return 0
    
  @property
  def length(self):
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
          SELECT COUNT(*) FROM samples
          WHERE processed = 0 
        ''')
        return cursor.fetchone()[0]
    except Exception as e:
      print(f"Error getting buffer length: {e}")
      return 0