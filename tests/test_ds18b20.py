import time
import board
from adafruit_ds18x20 import DS18X20
from adafruit_onewire.bus import OneWireBus

# Initialize one-wire bus on GPIO pin (typically GPIO4 on Raspberry Pi)
ow_bus = OneWireBus(board.D4)  # Change to your GPIO pin if different

# Scan for all DS18x20 devices on the bus
ds18_devices = DS18X20.scan_devices(ow_bus)

# Create DS18X20 object with the first found device
if ds18_devices:
    sensor = DS18X20(ow_bus, ds18_devices[0])
    
    # Read and print the temperature
    temperature_c = sensor.temperature
    temperature_f = temperature_c * 9 / 5 + 32
    print(f"Temperature: {temperature_c:.2f}°C ({temperature_f:.2f}°F)")
else:
    print("No DS18X20 devices found!")