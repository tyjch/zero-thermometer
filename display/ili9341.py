import board
import digitalio
import adafruit_rgb_display.ili9341 as ili9341
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import time

class ILI9341:
    
    def __init__(
        self,
        dc_pin    : int = 24,
        cs_pin    : int = 8,
        rst_pin   : Optional[int] = 25,
        rotation  : int = 270,
        font_size : int = 64,
        precision : int = 2,
        font_path : str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ):
        # Initialize the display
        self._display = ili9341.ILI9341(
            board.SPI(),
            cs       = digitalio.DigitalInOut(board.CE0),
            dc       = digitalio.DigitalInOut(board.D25),
            rst      = digitalio.DigitalInOut(board.D24), 
            baudrate = 24000000,
            rotation = rotation
        )
        
        self.font_size = font_size
        self.font_path = font_path
        
        # Determine actual dimensions based on rotation
        if rotation % 180 == 90:  # 90 or 270 degrees
            self.width = 320
            self.height = 240
        else:  # 0 or 180 degrees
            self.width = 240
            self.height = 320
        
        logger.info(f"Creating image with dimensions: {self.width}x{self.height}")
        # Use WHITE for background since colors are inverted
        self.image = Image.new("RGB", (self.width, self.height), (255, 255, 255))
        self.draw = ImageDraw.Draw(self.image)
        
        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except IOError:
            logger.warning(f"Could not load font {font_path}, using default")
            self.font = ImageFont.load_default()
    
    def show_value(self, value: float):
        self.draw.rectangle((0, 0, self.width, self.height), fill=(255, 255, 255))
        self.draw.text(
            (self.width // 2, self.height // 2),
            f'{value:.2f} \u2109',
            font=self.font,
            fill=(0, 0, 0),  # Black text
            anchor="mm"  # Center the text
        )
        
        try:
            self._display.image(self.image)
            logger.info("Image sent to display")
        except ValueError as e:
            logger.error(f"Display error: {e}")
            logger.error(f"Image dimensions: {self.image.size}")
    
