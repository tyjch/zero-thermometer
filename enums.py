from enum import Enum

class Event(Enum):
  NONE        =  0
  DIVERGENCE  = -1
  CONVERGENCE =  1
  DISCONNECT  = -2
  RECONNECT   =  2

class Temperature(Enum):
  COLD    = -2
  COOL    = -1
  AVERAGE =  0
  WARM    =  1
  HOT     =  2

class Measurable(Enum):
  TEMPERATURE = 0
  HUMIDITY    = 1
