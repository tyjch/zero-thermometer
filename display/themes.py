from dataclasses import dataclass
from sensors import Measurement
from enums import Temperature

@dataclass
class ColorStyle:
  text_color : Tuple(int, int, int) = (255, 255, 255)
  bg_color   : Tuple(int, int, int) = (0, 0, 0)


color_styles = {
  Temperature.COLD    : ColorStyle(text_color=( 50,  50, 150)),
  Temperature.COOL    : ColorStyle(text_color=(125, 200, 225)),
  Temperature.AVERAGE : ColorStyle(text_color=(250, 250, 200)),
  Temperature.WARM    : ColorStyle(text_color=(250, 125,  75)),
  Temperature.HOT     : ColorStyle(text_color=(150,   0,  50)),
}
  
