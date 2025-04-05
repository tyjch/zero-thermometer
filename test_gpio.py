#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# GPIO pin connected to the backlight
BACKLIGHT_PIN = 18

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)

# Create PWM instance
pwm = GPIO.PWM(BACKLIGHT_PIN, 100)  # 100Hz frequency
pwm.start(0)  # Start with 0% duty cycle (off)

try:
    print("Testing backlight PWM control...")
    
    # Turn on to 100%
    print("Setting backlight to 100%")
    pwm.ChangeDutyCycle(100)
    time.sleep(2)
    
    # Dim to 50%
    print("Setting backlight to 50%")
    pwm.ChangeDutyCycle(50)
    time.sleep(2)
    
    # Dim to 10%
    print("Setting backlight to 10%")
    pwm.ChangeDutyCycle(10)
    time.sleep(2)
    
    # Turn off
    print("Turning backlight off")
    pwm.ChangeDutyCycle(0)
    time.sleep(2)
    
    # Fade effect
    print("Fading up...")
    for i in range(0, 101, 5):
        pwm.ChangeDutyCycle(i)
        time.sleep(0.1)
    
    print("Fading down...")
    for i in range(100, -1, -5):
        pwm.ChangeDutyCycle(i)
        time.sleep(0.1)
        
    print("Test complete")
    
except KeyboardInterrupt:
    pass
finally:
    # Clean up
    pwm.stop()
    GPIO.cleanup()