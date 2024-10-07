import time
import board
from digitalio import DigitalInOut
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

class SpinnerDisplay:
    def __init__(self):
        # Create the display
        self.cs_pin = DigitalInOut(board.CE0)
        self.dc_pin = DigitalInOut(board.D25)
        self.reset_pin = DigitalInOut(board.D24)
        self.width = 240
        self.height = 240
        self.BAUDRATE = 24000000

        # Initialize the interface
        spi = board.SPI()

        # Initialize display
        self.disp = st7789.ST7789(
            spi,
            height=240,
            y_offset=80,
            rotation=180,
            cs=self.cs_pin,
            dc=self.dc_pin,
            rst=self.reset_pin,
            baudrate=self.BAUDRATE,
        )

        # Turn on the Backlight
        self.backlight = DigitalInOut(board.D26)
        self.backlight.switch_to_output()
        self.backlight.value = True

        # Create blank image for drawing
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Set default font
        self.set_default_font()

    def set_default_font(self):
        """Set the default font for displaying text."""
        self.font = ImageFont.load_default()

    def clear_display(self):
        """Clears the display by filling it with a black rectangle."""
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))

    def update_display(self):
        """Update the display with the current image buffer."""
        self.disp.image(self.image)

    def display_spinner(self, spinner_chars, delay=0.1):
        """Animates a spinner on the display."""
        center_x = self.width // 2
        center_y = self.height // 2

        while True:
            for char in spinner_chars:
                # Clear the display
                self.clear_display()

                # Draw the spinner character at the center of the screen
                text_size = self.draw.textsize(char, font=self.font)
                text_x = center_x - text_size[0] // 2
                text_y = center_y - text_size[1] // 2
                self.draw.text((text_x, text_y), char, font=self.font, fill=(255, 255, 255))

                # Update the display
                self.update_display()

                # Pause for a short time to create animation effect
                time.sleep(delay)

# Example usage
if __name__ == "__main__":
    # Initialize the display
    spinner_display = SpinnerDisplay()

    # Define the spinner characters
    spinner_chars = ['|', '/', '-', '\\']

    # Start the spinner animation
    spinner_display.display_spinner(spinner_chars)
