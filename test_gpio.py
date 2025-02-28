import RPi.GPIO as GPIO
import time

# Set the GPIO mode
GPIO.setmode(GPIO.BCM)

# Setup GPIO26 as output
GPIO.setup(26, GPIO.OUT)

# Set it HIGH
GPIO.output(26, GPIO.HIGH)

print("GPIO26 set HIGH. Measuring voltage for 60 seconds...")
time.sleep(60)

# Cleanup
GPIO.cleanup()
print("Done")