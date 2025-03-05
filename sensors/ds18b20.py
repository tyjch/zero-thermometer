import os
import glob
import time
import RPi.GPIO as GPIO

class DS18B20:
    def __init__(self, power_pin=26, bias=0):  # GPIO26 is pin 37
        self.power_pin = power_pin
        self.bias = bias
        
        # Setup GPIO for power
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.power_pin, GPIO.OUT)
        GPIO.output(self.power_pin, GPIO.HIGH)  # Provide 3.3V power
        
        # Wait for the sensor to initialize
        time.sleep(2)
        
        # Define the path for device files
        self.base_dir = '/sys/bus/w1/devices/'
        try:
            self.device_folder = glob.glob(self.base_dir + '28*')[0]
            self.device_file = self.device_folder + '/w1_slave'
        except IndexError:
            raise Exception("No DS18B20 sensor found. Check connections and ensure 1-Wire is enabled in /boot/config.txt")
    
    def read_temp_raw(self):
        try:
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
            return lines
        except Exception as e:
            print(f"Error reading sensor: {e}")
            return None
    
    def read_temp(self):
        lines = self.read_temp_raw()
        if not lines:
            return None
            
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.read_temp_raw()
        
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return {'celsius': temp_c, 'fahrenheit': temp_f + self.bias}
        
        return None
    
    def cleanup(self):
        GPIO.output(self.power_pin, GPIO.LOW)
        GPIO.cleanup()

