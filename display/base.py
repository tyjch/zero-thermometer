import board
import digitalio
import adafruit_rgb_display
from abc import ABC, abstractmethod
from typing import Optional, Dict, Tuple, List, Any, Type
from PIL import Image, ImageDraw, ImageFont
from sensors.base import Measurement


class Display(ABC):
    def __init__(
        self,
        width            : int,
        height           : int,
        dc_pin           : int = 24,
        cs_pin           : int = 8,
        rst_pin          : Optional[int] = 25,
        rotation         : int = 0,
        baudrate         : int = 64000000,
        precision        : int = 2
    ):
        self.width            = width
        self.height           = height       
        self.dc_pin           = dc_pin
        self.cs_pin           = cs_pin
        self.rst_pin          = rst_pin
        self.rotation         = rotation
        self.font_size        = font_size
        self.font_path        = font_path
        self.background_color = background_color
        self.text_color       = text_color
        self.baudrate         = baudrate
        self.precision        = precision
        self.display          = None
        
        self.image = Image.new("RGB", (width, height), background_color)
        self.draw  = ImageDraw.Draw(self.image)
        
        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except IOError:
            self.font = ImageFont.load_default()
    
    @abstractmethod
    def _create_display(self) -> None:
        """Create the specific display hardware"""
        pass
    
    def initialize(self) -> None:
        """Initialize the display hardware"""
        spi = board.SPI()
        dc = digitalio.DigitalInOut(getattr(board, f"D{self.dc_pin}"))
        cs = digitalio.DigitalInOut(getattr(board, f"D{self.cs_pin}"))
        rst = None

        if self.rst_pin is not None:
            rst = digitalio.DigitalInOut(getattr(board, f"D{self.rst_pin}"))
            
        self._create_display(spi, dc, cs, rst)
    
    def show(self) -> None:
        """Update the display with current image"""
        if self.display:
            self.display.image(self.image)
    
    def clear(self) -> None:
        self.draw.rectangle((0, 0, self.width, self.height), fill=self.background_color)
    
    def draw_text(self, x: int, y: int, text: str, color: Optional[Tuple[int, int, int]]=None, anchor: str="lt") -> None:
        self.draw.text((x, y), text, font=self.font, fill=color or self.text_color, anchor=anchor)
    
    def draw_centered_text(self, text: str, color: Optional[Tuple[int, int, int]]=None) -> None:
        self.draw_text(self.width // 2, self.height // 2, text, color, anchor="mm")
    
    def draw_measurement(self, measurement: Measurement, formatter: Optional['DisplayFormatter']=None) -> None:
        self.clear()
        
        # Format the measurement text
        formatted_value = f"{measurement.value:.{self.precision}f} {measurement.unit}"
        
        # Apply formatting if provided
        if formatter:
            bg_color, text_color, formatted_value = formatter.format_measurement(measurement, self.precision)
            self.draw.rectangle((0, 0, self.width, self.height), fill=bg_color)
        else:
            text_color = self.text_color
        
        # Draw centered text
        self.draw_centered_text(formatted_value, text_color)
        
        # Update the display
        self.show()
    
    def update_settings(self, config: Dict[str, Any]) -> None:
        """Update display settings from config"""
        if 'font_size' in config:
            self.font_size = config['font_size']
            try:
                self.font = ImageFont.truetype(self.font_path, self.font_size)
            except IOError:
                self.font = ImageFont.load_default()
        
        if 'background_color' in config:
            self.background_color = tuple(config['background_color'])
        
        if 'text_color' in config:
            self.text_color = tuple(config['text_color'])
        
        if 'precision' in config:
            self.precision = config['precision']