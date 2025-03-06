import board
import digitalio
import adafruit_rgb_display.ili9341 as ili9341
from typing import Optional, Tuple, Dict, Any
from .base import Display


class ILI9341(Display):
    # Adafruit PiTFT 2.2" HAT MINI display (ILI9341)
    
    def __init__(
        self,
        dc_pin           : int = 24,
        cs_pin           : int = 8,
        rst_pin          : Optional[int] = 25,
        rotation         : int = 90,
        font_size        : int = 24,
        background_color : Tuple[int, int, int] = (0, 0, 0),
        text_color       : Tuple[int, int, int] = (255, 255, 255)
    ):
        # ILI9341 is 240x320, but we rotate it
        if rotation in [90, 270]:
            super().__init__(320, 240, rotation, font_size, background_color=background_color, text_color=text_color)
        else:
            super().__init__(240, 320, rotation, font_size, background_color=background_color, text_color=text_color)
        
        self.dc_pin  = dc_pin
        self.cs_pin  = cs_pin
        self.rst_pin = rst_pin
        self.display = None
    
    def initialize(self) -> None:
        spi = board.SPI()
        dc  = digitalio.DigitalInOut(getattr(board, f"D{self.dc_pin}"))
        cs  = digitalio.DigitalInOut(getattr(board, f"D{self.cs_pin}"))
        rst = None

        if self.rst_pin is not None:
            rst = digitalio.DigitalInOut(getattr(board, f"D{self.rst_pin}"))
        
        self.display = ili9341.ILI9341(
            spi,
            cs       = cs,
            dc       = dc,
            rst      = rst,
            rotation = self.rotation,
            baudrate = 64000000
        )
    
    def show(self) -> None:
        if self.display:
            self.display.image(self.image)