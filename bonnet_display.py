import board
import busio
import time
import smbus2 as smbus
from PIL import Image, ImageDraw, ImageFont, ImageOps
from digitalio import DigitalInOut
from adafruit_rgb_display import st7789

# Color definitions as RGB tuples
COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "gray": (128, 128, 128),
    "light_gray": (211, 211, 211),
    "dark_gray": (169, 169, 169),
    "gold": (255, 215, 0),
    "silver": (192, 192, 192),
}

class DisplayConfig:
    def __init__(self, font_path=None, font_size=18, border_size=2):
        self.font_path = font_path
        self.font_size = font_size
        self.border_size = border_size

    def get_font_path(self):
        return self.font_path

    def get_font_size(self):
        return self.font_size

    def get_border_size(self):
        return self.border_size


# Function to tint the fan icon based on status and preserve transparency
def tint_icon(icon, color):
    # Separate the RGB and alpha channels
    icon_rgb = icon.convert("RGB")
    icon_alpha = icon.getchannel("A")

    # Create a solid color image (RGBA) to apply as a tint
    solid_color = Image.new("RGBA", icon.size, color)

    # Combine the original alpha channel with the solid color image
    colored_icon = Image.composite(solid_color, icon_rgb, icon_alpha)

    # Restore the alpha channel to preserve transparency
    colored_icon.putalpha(icon_alpha)

    return colored_icon

class BonnetDisplay:
    def __init__(self, configuration):

        self.config_manager = configuration

        # Create the display
        self.cs_pin = DigitalInOut(board.CE0)
        self.dc_pin = DigitalInOut(board.D25)
        self.reset_pin = DigitalInOut(board.D24)
        self.width = 240
        self.height = 240
        self.BAUDRATE = 24000000

        # Initialize the interface
        spi = board.SPI()
        # Initialize display.
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
        backlight = DigitalInOut(board.D26)
        backlight.switch_to_output()
        backlight.value = True
        # Set the font using config_manager
        self.set_font(self.config_manager.get_font_path(), self.config_manager.get_font_size())

        self.font = None  # Assume you will load a font here
        self.oled_lines = [""] * 5  # List to hold up to 5 lines of text
        self.image = Image.new('RGB', (self.width, self.height), "black")
        self.draw = None  # Will be initialized based on `ImageDraw.Draw`

    def set_font(self, font_path=None, font_size=16):
        print(font_path, font_size)
        if font_path:
            self.font = ImageFont.truetype(font_path, font_size)
        else:
            self.font = ImageFont.load_default()

    def set_brightness(self, color_name, brightness_factor):
        """ Simulate adjusting brightness (returns modified color) """
        # You would implement actual color/brightness logic here
        return color_name

    def display_rows_center(self, texts, current_page, fan_running=False, color_name="white",
                            brightness_factor=1.0, justification='center'):
        num_lines = min(5, len(texts))
        line_height = self.height // num_lines

        # Get color with brightness applied
        color = self.set_brightness(color_name, brightness_factor)

        for i in range(num_lines):
            text = texts[i]
            self.oled_lines[i] = text
            bbox = self.draw.textbbox((0, 0), text, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate horizontal position based on justification
            if justification == 'left':
                x_position = 0
            elif justification == 'right':
                x_position = self.width - text_width
            else:  # default to center
                x_position = (self.width - text_width) // 2

            position = (x_position, i * line_height + (line_height - text_height) // 2)
            self.draw.text(position, text, font=self.font, fill=color)

        # Handle fan icon if needed for current_page == 0
        if current_page == 0:
            fan_icon = Image.open("fan_icon.png").convert("RGBA").resize((48, 48))  # Load fan icon
            if fan_running:
                fan_color = (0, 255, 0, 255)  # Green (RGBA)
            else:
                fan_color = (255, 255, 255, 255)  # White (RGBA)
            # Tint the fan icon based on fan status (you'd implement tint_icon function)
            colored_fan_icon = self.tint_icon(fan_icon, fan_color)
            self.image.paste(colored_fan_icon, (10, 190), colored_fan_icon.split()[-1])

        # To display this image, it would be passed to an external method like `disp.image()`
