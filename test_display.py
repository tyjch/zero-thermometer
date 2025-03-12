import time
import board
import digitalio
import adafruit_rgb_display.ili9341 as ili9341
from PIL import Image, ImageDraw, ImageFont

# Configure pins for Adafruit PiTFT 2.2"
cs_pin = board.CE0
dc_pin = board.D25
reset_pin = board.D24

# Initialize the display
spi = board.SPI()
display = ili9341.ILI9341(
    spi,
    rotation=270,
    cs=digitalio.DigitalInOut(cs_pin),
    dc=digitalio.DigitalInOut(dc_pin),
    rst=digitalio.DigitalInOut(reset_pin),
    baudrate=24000000
)

# Set dimensions
if display.rotation % 180 == 90:
    width, height = 320, 240
else:
    width, height = 240, 320

# Load font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
except IOError:
    font = ImageFont.load_default()

# Function to create different test screens
def create_test_screen(number):
    colors = [
        (0, 0, 0),    # Black
        (255, 0, 0),  # Red
        (0, 255, 0),  # Green
        (0, 0, 255)   # Blue
    ]
    
    bg_color = colors[number % len(colors)]
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # White text showing the test number
    draw.text(
        (width//2, height//2),
        f"Test Screen {number}",
        font=font,
        fill=(255, 255, 255),
        anchor="mm"
    )
    
    # Current time
    current_time = time.strftime("%H:%M:%S")
    draw.text(
        (width//2, height//2 + 40),
        current_time,
        font=font,
        fill=(255, 255, 255),
        anchor="mm"
    )
    
    return image

# Cycle through different test screens
try:
    print("Cycling through test screens. Press Ctrl+C to exit.")
    counter = 0
    while True:
        image = create_test_screen(counter % 4)
        display.image(image)
        print(f"Displayed test screen {counter % 4}")
        counter += 1
        time.sleep(3)  # Show each screen for 3 seconds
except KeyboardInterrupt:
    print("Exiting...")