# display/base.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Tuple, List, Any
from PIL import Image, ImageDraw, ImageFont

from sensors.base import Measurement


class Display(ABC):
    """Abstract base class for all displays"""
    
    def __init__(
        self,
        width: int,
        height: int,
        rotation: int = 0,
        font_size: int = 24,
        font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        background_color: Tuple[int, int, int] = (0, 0, 0),
        text_color: Tuple[int, int, int] = (255, 255, 255)
    ):
        self.width = width
        self.height = height
        self.rotation = rotation
        self.font_size = font_size
        self.font_path = font_path
        self.background_color = background_color
        self.text_color = text_color
        
        # Create a PIL Image and ImageDraw object
        self.image = Image.new("RGB", (width, height), background_color)
        self.draw = ImageDraw.Draw(self.image)
        
        # Load font
        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except IOError:
            # Fallback to default font
            self.font = ImageFont.load_default()
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the display hardware"""
        pass
    
    @abstractmethod
    def show(self) -> None:
        """Update the display with current image"""
        pass
    
    def clear(self) -> None:
        """Clear the display"""
        self.draw.rectangle((0, 0, self.width, self.height), fill=self.background_color)
    
    def draw_text(self, x: int, y: int, text: str, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Draw text at the specified position"""
        self.draw.text((x, y), text, font=self.font, fill=color or self.text_color)
    
    def draw_measurements(self, measurements: List[Measurement], title: Optional[str] = None) -> None:
        """Draw a list of measurements on the display"""
        self.clear()
        
        y_offset = 5
        
        # Draw title if provided
        if title:
            self.draw_text(5, y_offset, title)
            y_offset += self.font_size + 5
        
        # Draw each measurement
        for measurement in measurements:
            sensor_name = getattr(measurement, 'sensor_name', measurement.sensor_id)
            value_text = f"{sensor_name}: {measurement.value:.1f} {measurement.unit}"
            self.draw_text(5, y_offset, value_text)
            y_offset += self.font_size + 5
        
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