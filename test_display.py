import time
import board
import digitalio
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Configuration for CS and DC pins
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

# Config for display baudrate
BAUDRATE = 24000000

# Setup SPI bus using hardware SPI
spi = busio.SPI(board.SCK, MOSI=board.MOSI)

# Create the ST7789 display:
display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,  # Using the dimensions from your error message
    height=240,
    rotation=90,  # You may need to adjust this based on your display orientation
    x_offset=53,  # The ST7789 often needs an offset - adjust if needed
    y_offset=40,  # The ST7789 often needs an offset - adjust if needed
)

# Create blank image for drawing with correct dimensions
width = display.width
height = display.height
image = Image.new("RGB", (width, height))

# Get drawing object to draw on image
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

# Load a TTF font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except IOError:
    # If the font file isn't found, use a default font
    font = ImageFont.load_default()

# Draw text
draw.text((10, 10), "Hello World!", font=font, fill=(255, 255, 255))

# Display image
display.image(image)

# Keep the display on for 10 seconds
time.sleep(10)