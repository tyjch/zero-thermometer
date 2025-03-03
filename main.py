import os
import json
import board
import digitalio
import requests
from pprint import pprint
from enum import Enum
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
#from discord import send_message
from sensor import DS18B20

load_dotenv()

# DISPLAY --------------------------------------------------------------------------------
cs_pin    = digitalio.DigitalInOut(board.CE0)
dc_pin    = digitalio.DigitalInOut(board.D25)
reset_pin = None
BAUDRATE  = 64000000

spi     = board.SPI()
display = st7789.ST7789(
    spi,
    cs       = cs_pin,
    dc       = dc_pin,
    rst      = reset_pin,
    baudrate = BAUDRATE,
    width    = 135,
    height   = 240,
    x_offset = 53,
    y_offset = 40,
)

image = Image.new('RGB', (display.height, display.width))
draw  = ImageDraw.Draw(image)
font  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True
rotation = 90

# PARAMETERS -----------------------------------------------------------------------------------
 
def get_parameters(json_path='params.json'):
  """
  Requests a json file from a gist and uses that to update the parameter file
  If that fails, then it attempts to load parameters from the file.
  If that fails, then an error is raised
  """
  try:
    response = requests.get(os.getenv('parameters_url'))
    if response.status_code == 200:
      params = response.json()
      with open(json_path, 'w') as file:
        json.dump(params, file, indent=4)
      
  except requests.exceptions.ConnectionError:
    with open(json_path, 'r') as file:
      params = json.load(file)

  return params

params = get_parameters()

# TEMPERATURE SENSOR ---------------------------------------------------------------------------

thermometer = DS18B20(bias=params['sensor']['bias'])

TEMPERATURE_SYMBOLS = {
  'fahrenheit' : '\u2109',
  'celsius'    : '\u2103'
}

class Temperature(Enum):
  COLD    = -2
  COOL    = -1
  AVERAGE =  0
  WARM    =  1
  HOT     =  2

temp_map = {
  Temperature.COLD    : 'cold',
  Temperature.COOL    : 'cool',
  Temperature.AVERAGE : 'average',
  Temperature.WARM    : 'warm',
  Temperature.HOT     : 'hot'
}

def get_temp_status(value):
  t = params['temperature']
  if t['cool'] < value < t['warm']:
    return Temperature.AVERAGE
  elif value < t['cold']:
    return Temperature.COLD
  elif value > t['hot']:
    return Temperature.HOT
  else:
    if value < t['average']:
      return Temperature.COOL
    else:
      return Temperature.WARM

def get_display_colors(temp_status: str):
  return params['display']['colors'][temp_map[temp_status]]

def display_temperature(value, unit='fahrenheit', text_color='#FFFFFF', bg_color='#000000'):
  print('Displayed temperature')
  display_text = f'{value:.1f} {TEMPERATURE_SYMBOLS.get(unit)}'
  draw.rectangle((0,0, display.height, display.width), outline=0, fill=bg_color)
  draw.text((25,25), display_text, font=font, fill=text_color)
  display.image(image, rotation)

# MESSAGING --------------------------------------------------------------------------------------------------------
# Should only message once per shift between temperature thresholds
# Should also limit how often messages can be sent, since it may hover around a threshold

class Event(Enum):
  NONE        =  0
  DIVERGENCE  = -1
  CONVERGENCE =  1
  DISCONNECT  = -2
  RECONNECT   =  2
  

class Monitor():

  def __init__(self, disconnect_threshold=0.1, reconnect_threshold=1):
    self.cooldown             = params['messaging']['cooldown']
    self.disconnect_threshold = disconnect_threshold
    self.reconnect_threshold  = reconnect_threshold
    
    events = params['messaging']['events']
    self.policies  = {
      Event.CONVERGENCE : events['convergence'],
      Event.DIVERGENCE  : events['divergence'],
      Event.DISCONNECT  : events['disconnect'],
      Event.RECONNECT   : events['reconnect']
    }

    self.previous_temp   = None
    self.previous_status = None
    self.current_temp    = None
    self.current_status  = None
    
    self.last_event        = Event.NONE
    self.messaged          = False
    self.last_messaged     = None
    self.temperature_floor = 95

    self.webhook = os.getenv('discord_webhook')

  def add_value(self, value):
    self.previous_temp   = self.current_temp
    self.previous_status = self.current_status
    self.current_temp    = value
    self.current_status  = get_temp_status(value)
    self.determine_event()

  def did_reconnect(self):
    if (self.previous_temp <= self.temperature_floor) and (self.current_temp >= self.temperature_floor):
      return True

  def did_disconnect(self):
    if (self.previous_temp >= self.temperature_floor) and (self.current_temp <= self.temperature_floor):
      return True

  def is_converging(self):
    if self.previous_status == self.current_status:
      return False
    else:
      delta = self.get_delta()
      if (delta > 0) and (self.previous_status in (Temperature.COLD, Temperature.COOL)):
        return True
      elif (delta < 0) and (self.previous_status in (Temperature.HOT, Temperature.WARM)):
        return True
      else:
        return False

  def is_diverging(self):
    if self.previous_status == self.current_status:
      return False
    else:
      delta = self.get_delta()
      if (delta > 0) and (self.previous_status in (Temperature.AVERAGE, Temperature.WARM)):
        return True
      elif (delta < 0) and (self.previous_status in (Temperature.AVERAGE, Temperature.COOL)):
        return True
      else:
        return False

  def determine_event(self):
    if self.previous_status == self.current_status:
      self.last_event = Event.NONE
    elif self.did_reconnect():
      self.last_event = Event.RECONNECT
    elif self.did_disconnect():
      self.last_event = Event.DISCONNECT
    elif self.is_converging():
      self.last_event = Event.CONVERGENCE
    elif self.is_diverging():
      self.last_event = Event.DIVERGENCE
    return self.last_event

  def get_delta(self):
    return self.current_temp - self.previous_temp


def tick():
  temperature = thermometer.read_temp()['fahrenheit']
  print(temperature)
  status = get_temp_status(temperature)
  print(status)
  theme  = get_display_colors(status)
  print(theme)
  display_temperature(temperature, text_color=theme['font'], bg_color=theme['bg'])
  

if __name__ == '__main__':
  while True:
    tick()