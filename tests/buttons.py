from gpiozero import Button
from signal import pause
import time

# Initialize the buttons
up_button = Button(12)  # Assuming the UP button is connected to GPIO pin 17
dn_button = Button(16)  # Assuming the DN button is connected to GPIO pin 27

# State tracking to control simultaneous press and hold behavior
both_held = False

# Callback functions for button events
def up_pressed():
    global both_held
    if not both_held:
        print("UP button pressed")

def up_held():
    global both_held
    if not both_held:
        print("UP button held for 2 seconds")

def dn_pressed():
    global both_held
    if not both_held:
        print("DN button pressed")

def dn_held():
    global both_held
    if not both_held:
        print("DN button held for 2 seconds")

def check_both_held():
    global both_held
    if up_button.is_held and dn_button.is_held:
        both_held = True
        print("Both buttons held for 2 seconds")
        time.sleep(2)  # Simulate the time holding period
        both_held = False

# Attach event listeners to buttons
up_button.when_pressed = up_pressed
up_button.when_held = up_held

dn_button.when_pressed = dn_pressed
dn_button.when_held = dn_held

# Continuously check if both buttons are being held
while True:
    check_both_held()
    time.sleep(0.1)  # Slight delay to avoid high CPU usage
