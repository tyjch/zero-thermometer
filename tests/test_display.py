import digitalio
import board
import time
import busio
import adafruit_rgb_display.ili9341 as ili9341
from adafruit_rgb_display.rgb import color565

# Configuration for CS, DC, and RESET pins
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

# Create SPI connection
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Create the ILI9341 display:
display = ili9341.ILI9341(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=24000000,
    width=320,     # 2.4" PiTFT dimensions
    height=240,
    rotation=90    # Adjust rotation as needed
)

# Initialize display
display.fill(color565(0, 0, 0))  # Clear to black
time.sleep(1)

# Backlight control (if applicable)
try:
    backlight = digitalio.DigitalInOut(board.D22)
    backlight.switch_to_output()
    backlight.value = True
except:
    print("Backlight control not available")

# Button setup (if applicable)
try:
    buttonA = digitalio.DigitalInOut(board.D23)
    buttonB = digitalio.DigitalInOut(board.D17)
    buttonA.switch_to_input()
    buttonB.switch_to_input()
except:
    print("Button control not available")

# Test color patterns
display.fill(color565(255, 0, 0))  # Red
time.sleep(1)
display.fill(color565(0, 255, 0))  # Green
time.sleep(1)
display.fill(color565(0, 0, 255))  # Blue
time.sleep(1)

# Main interaction loop
while True:
    try:
        if buttonA.value and buttonB.value:
            display.fill(color565(255, 255, 255))  # White when both pressed
            print('White')
        elif buttonA.value:
            display.fill(color565(255, 0, 0))  # Red when A pressed
            print('Red')
        elif buttonB.value:
            display.fill(color565(0, 0, 255))  # Blue when B pressed
            print('Blue')
        else:
            display.fill(color565(0, 255, 0))  # Green when no buttons pressed
            
            print('Green')   
    except Exception as e:
        print(e)