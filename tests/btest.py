import time
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Setup for display with updated settings
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)
BAUDRATE = 24000000

spi = board.SPI()
display = st7789.ST7789(
    spi,
    height=240,
    y_offset=80,
    rotation=180,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

# Setup for buttons
button_L = digitalio.DigitalInOut(board.D27)
button_L.direction = digitalio.Direction.INPUT
button_L.pull = digitalio.Pull.UP

button_R = digitalio.DigitalInOut(board.D23)
button_R.direction = digitalio.Direction.INPUT
button_R.pull = digitalio.Pull.UP

button_U = digitalio.DigitalInOut(board.D17)
button_U.direction = digitalio.Direction.INPUT
button_U.pull = digitalio.Pull.UP

button_D = digitalio.DigitalInOut(board.D22)
button_D.direction = digitalio.Direction.INPUT
button_D.pull = digitalio.Pull.UP

button_C = digitalio.DigitalInOut(board.D4)
button_C.direction = digitalio.Direction.INPUT
button_C.pull = digitalio.Pull.UP

button_A = digitalio.DigitalInOut(board.D5)
button_A.direction = digitalio.Direction.INPUT
button_A.pull = digitalio.Pull.UP

button_B = digitalio.DigitalInOut(board.D6)
button_B.direction = digitalio.Direction.INPUT
button_B.pull = digitalio.Pull.UP

# Configurable font size
FONT_SIZE = 24  # Adjust this for larger or smaller fonts

# Load a TrueType font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE)
except IOError:
    font = ImageFont.load_default()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Create blank image for drawing
image = Image.new("RGB", (240, 240))
draw = ImageDraw.Draw(image)

# Load fan icon (dummy path, replace with real path)
fan_icon = Image.open("fan_icon.png").resize((24, 24))

# State Variables
current_page = 0  # 0: Default, 1: Humidity Set, 2: Fan Stats, 3: Internal Stats, 4: External Stats
selected_value = None  # Track selected value on Humidity Set page (None, Max, Min)
is_editing = False  # Track if we are editing a value
last_activity_time = time.time()
timeout_seconds = 10  # Timeout to return to the default page
blink = False  # For blinking effect
last_blink_time = time.time()  # Track time for blinking

# Default values for display (these can be updated globally)
temp = 72.3
internal_humidity = 45.7
external_humidity = 40.2
fan_runtime = "00:00:00"
max_humidity = 60.0
min_humidity = 30.0


def draw_default_page():
    draw.rectangle((0, 0, 240, 240), fill=BLACK)

    # Draw Temperature, Internal, External Humidity, and Fan Runtime
    draw.text((10, 20), f"Temp {temp:.1f}F", font=font, fill=WHITE)
    draw.text((10, 60), f"Int {internal_humidity:.1f}%", font=font, fill=WHITE)
    draw.text((10, 100), f"Ext {external_humidity:.1f}%", font=font, fill=WHITE)

    # Draw the fan icon next to the fan runtime
    draw.bitmap((10, 140), fan_icon, fill=WHITE)
    draw.text((40, 140), fan_runtime, font=font, fill=WHITE)

    # Update the display
    display.image(image)


def draw_humidity_set_page():
    global blink

    draw.rectangle((0, 0, 240, 240), fill=BLACK)

    # Humidity Set Page - Max and Min values
    draw.text((10, 40), "Humidity Set", font=font, fill=WHITE)

    # Blinking logic for editing mode
    if is_editing:
        if blink:
            # Draw the blinking value
            if selected_value == "Max":
                draw.text((10, 80), "Max:", font=font, fill=WHITE)
                draw.text((100, 80), f"{max_humidity:.1f}%", font=font, fill=RED)
            elif selected_value == "Min":
                draw.text((10, 120), "Min:", font=font, fill=WHITE)
                draw.text((100, 120), f"{min_humidity:.1f}%", font=font, fill=RED)
        else:
            # Draw the labels without highlighting (blinking)
            draw.text((10, 80), "Max:", font=font, fill=WHITE)
            draw.text((100, 80), f"{max_humidity:.1f}%", font=font, fill=BLACK)
            draw.text((10, 120), "Min:", font=font, fill=WHITE)
            draw.text((100, 120), f"{min_humidity:.1f}%", font=font, fill=BLACK)
    else:
        # Normal display, highlight only the selected value
        if selected_value == "Max":
            draw.text((10, 80), "Max:", font=font, fill=WHITE)
            draw.text((100, 80), f"{max_humidity:.1f}%", font=font, fill=RED)
            draw.text((10, 120), "Min:", font=font, fill=WHITE)
            draw.text((100, 120), f"{min_humidity:.1f}%", font=font, fill=WHITE)
        elif selected_value == "Min":
            draw.text((10, 80), "Max:", font=font, fill=WHITE)
            draw.text((100, 80), f"{max_humidity:.1f}%", font=font, fill=WHITE)
            draw.text((10, 120), "Min:", font=font, fill=WHITE)
            draw.text((100, 120), f"{min_humidity:.1f}%", font=font, fill=RED)
        else:
            # No value selected, display both normally
            draw.text((10, 80), "Max:", font=font, fill=WHITE)
            draw.text((100, 80), f"{max_humidity:.1f}%", font=font, fill=WHITE)
            draw.text((10, 120), "Min:", font=font, fill=WHITE)
            draw.text((100, 120), f"{min_humidity:.1f}%", font=font, fill=WHITE)

    display.image(image)


def handle_button_press():
    global current_page, selected_value, is_editing, max_humidity, min_humidity, last_activity_time

    # Reset activity timeout
    last_activity_time = time.time()

    # Button logic for navigating and selecting options
    if current_page == 0:  # Default page
        if not button_R.value:  # Navigate to Humidity Set page
            current_page = 1
        elif not button_L.value:  # Navigate to External Stats page
            current_page = 4

    elif current_page == 1:  # Humidity Set page
        if not is_editing:
            if not button_A.value and selected_value is None:  # Highlight the Max value
                selected_value = "Max"
            elif not button_A.value and selected_value is not None:  # Enter edit mode
                is_editing = True
            elif not button_U.value or not button_D.value:  # Toggle between Max and Min
                selected_value = "Min" if selected_value == "Max" else "Max"
        else:
            if not button_U.value:  # Increase the value while in edit mode
                if selected_value == "Max":
                    max_humidity += 0.1
                elif selected_value == "Min":
                    min_humidity += 0.1
            elif not button_D.value:  # Decrease the value while in edit mode
                if selected_value == "Max":
                    max_humidity -= 0.1
                elif selected_value == "Min":
                    min_humidity -= 0.1
            elif not button_B.value:  # Save the value and exit edit mode
                is_editing = False
                selected_value = None  # Clear the selection

        if not button_R.value and not is_editing:  # Navigate to Fan Stats page
            current_page = 2
        elif not button_L.value and not is_editing:  # Navigate to Default page
            current_page = 0


def update_screen():
    global blink, last_blink_time

    # Update the screen based on the current page
    if current_page == 0:
        draw_default_page()
    elif current_page == 1:
        draw_humidity_set_page()

    # Handle blinking when in edit mode
    if is_editing and time.time() - last_blink_time > 0.5:  # 0.5 second interval for blinking
        blink = not blink  # Toggle the blink state
        last_blink_time = time.time()


# Main loop
while True:
    handle_button_press()  # Check button input
    update_screen()  # Draw the current page

    # Check for inactivity timeout
    if time.time() - last_activity_time > timeout_seconds:
        current_page = 0  # Return to default page
        selected_value = None
        is_editing = False

    time.sleep(0.1)