import time
import board
import adafruit_si7021

# Create the I2C interface
i2c = board.I2C()  # uses board.SCL and board.SDA

# Create the sensor object
sensor = adafruit_si7021.SI7021(i2c)

# Simple test loop
try:
    while True:
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
        
        # Convert to Fahrenheit if desired
        # temp_f = temperature * 9 / 5 + 32
        
        print(f"Temperature: {temperature:.1f} °C")
        print(f"Humidity: {humidity:.1f} %")
        print("-" * 20)
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\nExiting program")