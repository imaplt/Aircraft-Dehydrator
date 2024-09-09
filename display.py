import board
import busio
import time
import smbus2 as smbus
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from digitalio import DigitalInOut, Direction
from adafruit_rgb_display import st7789
from colorsys import hsv_to_rgb

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


class BONNETDisplay:
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

        # Create blank image for drawing.
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Set the font using config_manager
        self.set_font(self.config_manager.get_font_path(), self.config_manager.get_font_size())
        # self.set_font()

        # Initialize lines
        self.oled_lines = [""] * 5

    def reset_screen(self):
        self.disp.fill(0)
        self._clear_image()

    def clear_screen(self):
        self.disp.fill(0)
        self._clear_image()
        # Create blank image for drawing.
        width = self.disp.width
        height = self.disp.height
        image = Image.new("RGB", (width, height))

        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)

        # Clear display (fill with black)
        draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
        self.disp.image(image)

    def _clear_image(self):
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def set_font(self, font_path=None, font_size=16):
        if font_path:
            self.font = ImageFont.truetype(font_path, font_size)
        else:
            self.font = ImageFont.load_default()

    def get_max_characters(self):
        # Get the bounding box of a single character
        bbox = self.draw.textbbox((0, 0), "W", font=self.font)
        char_width = bbox[2] - bbox[0]
        # Calculate the maximum number of characters that can fit in the display width
        max_chars = self.width // char_width
        return max_chars

    def set_brightness(self, color_name, brightness_factor):
        """ Adjust brightness of the named color. """
        if color_name not in COLORS:
            raise ValueError(f"Color '{color_name}' not found!")

        color = COLORS[color_name]
        return tuple(int(c * brightness_factor) for c in color)

    def blink_text(self, text, color_name="white", brightness_factor=1.0, blink_speed=0.5, blink_times=5):
        color = self.set_brightness(color_name, brightness_factor)
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center the text on the screen
        x_position = (self.width - text_width) // 2
        y_position = (self.height - text_height) // 2

        # Blink the text
        for _ in range(blink_times):
            self.clear_screen()
            # Show text
            self.draw.text((x_position, y_position), text, font=self.font, fill=color)
            self.disp.image(self.image)
            time.sleep(blink_speed)

            # Clear text (make it disappear)
            self.clear_screen()
            self.disp.image(self.image)
            time.sleep(blink_speed)

    def fade_text(self, text, color_name="white", fade_in_time=2.0, fade_out_time=2.0, steps=10):
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center the text on the screen
        x_position = (self.width - text_width) // 2
        y_position = (self.height - text_height) // 2

        # Fade in
        for i in range(steps + 1):
            brightness_factor = i / steps
            color = self.set_brightness(color_name, brightness_factor)
            self.clear_screen()
            self.draw.text((x_position, y_position), text, font=self.font, fill=color)
            self.disp.image(self.image)
            time.sleep(fade_in_time / steps)

        # Pause before fade-out
        time.sleep(0.5)

        # Fade out
        for i in range(steps + 1):
            brightness_factor = 1.0 - (i / steps)
            color = self.set_brightness(color_name, brightness_factor)
            self.clear_screen()
            self.draw.text((x_position, y_position), text, font=self.font, fill=color)
            self.disp.image(self.image)
            time.sleep(fade_out_time / steps)

    def display_text_center(self, text, color_name="white", brightness_factor=1.0, justification='center'):
        self.clear_screen()

        # Get color with brightness applied
        color = self.set_brightness(color_name, brightness_factor)

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

        position = (x_position, (self.height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=color)
        self.disp.image(self.image)

    def display_default_four_rows(self, color_name="white", brightness_factor=1.0):
        self.oled_lines = ["Internal:", "reading...", "External:", "reading..."]
        self.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."], color_name,
                                      brightness_factor, justification='left')

    def display_four_rows_center(self, texts, color_name="white", brightness_factor=1.0, justification='center'):
        self.clear_screen()
        num_lines = min(4, len(texts))
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
        self.disp.image(self.image)

    def update_line(self, line_number, text, color_name="white", brightness_factor=1.0, justification='center'):
        if line_number < 0 or line_number >= 5:
            raise ValueError("line_number must be between 0 and 4")

        self.oled_lines[line_number] = text

        # Get color with brightness applied
        color = self.set_brightness(color_name, brightness_factor)

        # Clear the specific line area
        line_height = self.height // 4
        y_position = line_number * line_height
        self.draw.rectangle((0, y_position, self.width, y_position + line_height), outline=0, fill=0)

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

        position = (x_position, y_position + (line_height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=color)

        self.disp.image(self.image)

    def display_text_center_with_border(self, text, color_name="white", brightness_factor=1.0):
        self.clear_screen()

        # Get color with brightness applied
        color = self.set_brightness(color_name, brightness_factor)

        border_size = self.config_manager.get_border_size()
        self.draw.rectangle((border_size, border_size, self.width - border_size - 1, self.height - border_size - 1),
                            outline=color, fill=0)
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((self.width - text_width) // 2, (self.height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=color)
        self.disp.image(self.image)


class SSD1306Display:
    def __init__(self, configuration, width=128, height=64, i2c_address=0x3C):
        self.width = width
        self.height = height
        self.i2c_address = i2c_address
        self.config_manager = configuration

        # Initialize I2C interface.
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Initialize display.
        self.disp = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, self.i2c, addr=self.i2c_address)
        # Create blank image for drawing.
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Set the font using config_manager
        # self.set_font(self.config_manager.get_font_path(), self.config_manager.get_font_size())
        self.set_font()

        # Initialize lines
        self.oled_lines = [""] * 4

    def reset_screen(self):
        self.disp.fill(0)
        self.disp.show()
        self._clear_image()

    def clear_screen(self):
        self.disp.fill(0)
        self.disp.show()
        self._clear_image()

    def _clear_image(self):
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def set_font(self, font_path=None, font_size=10):
        if font_path:
            self.font = ImageFont.truetype(font_path, font_size)
        else:
            self.font = ImageFont.load_default()

    def get_max_characters(self):
        # Get the bounding box of a single character
        bbox = self.draw.textbbox((0, 0), "W", font=self.font)
        char_width = bbox[2] - bbox[0]
        # Calculate the maximum number of characters that can fit in the display width
        max_chars = self.width // char_width
        return max_chars

    # The justification parameter can be 'left', 'right', or 'center' (default).
    def display_text_center(self, text, justification='center'):
        self.clear_screen()
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

        position = (x_position, (self.height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.show()

    def display_default_four_rows(self):
        # Yeah, I know. I could make this prettier
        self.oled_lines = ["Internal:", "reading...", "External:", "reading..."]
        self.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."], justification='left')

    def display_four_rows_center(self, texts, justification='center'):
        self.clear_screen()
        num_lines = min(4, len(texts))
        line_height = self.height // num_lines
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
            self.draw.text(position, text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.show()

    def update_line(self, line_number, text, justification='center'):
        if line_number < 0 or line_number >= 4:
            raise ValueError("line_number must be between 0 and 3")

        self.oled_lines[line_number] = text

        # Clear the specific line area
        line_height = self.height // 4
        y_position = line_number * line_height
        self.draw.rectangle((0, y_position, self.width, y_position + line_height), outline=0, fill=0)

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

        position = (x_position, y_position + (line_height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=255)

        self.disp.image(self.image)
        self.disp.show()

    def display_text_center_with_border(self, text):
        self.clear_screen()
        border_size = self.config_manager.get_border_size()
        self.draw.rectangle((border_size, border_size, self.width - border_size - 1, self.height - border_size - 1),
                            outline=255, fill=0)
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((self.width - text_width) // 2, (self.height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.show()


class LCD2004Display:
    def __init__(self, addr=0x27, bl=1):
        self.BUS = smbus.SMBus(1)
        self.LCD_ADDR = addr
        self.BLEN = bl
        self._init_display()
        self.lcd_lines = [""] * 4

    def _write_word(self, addr, data):
        temp = data
        if self.BLEN == 1:
            temp |= 0x08
        else:
            temp &= 0xF7
        self.BUS.write_byte(addr, temp)

    def _send_command(self, comm):
        buf = comm & 0xF0
        buf |= 0x04
        self._write_word(self.LCD_ADDR, buf)
        time.sleep(0.002)
        buf &= 0xFB
        self._write_word(self.LCD_ADDR, buf)

        buf = (comm & 0x0F) << 4
        buf |= 0x04
        self._write_word(self.LCD_ADDR, buf)
        time.sleep(0.002)
        buf &= 0xFB
        self._write_word(self.LCD_ADDR, buf)

    def _send_data(self, data):
        buf = data & 0xF0
        buf |= 0x05
        self._write_word(self.LCD_ADDR, buf)
        time.sleep(0.002)
        buf &= 0xFB
        self._write_word(self.LCD_ADDR, buf)

        buf = (data & 0x0F) << 4
        buf |= 0x05
        self._write_word(self.LCD_ADDR, buf)
        time.sleep(0.002)
        buf &= 0xFB
        self._write_word(self.LCD_ADDR, buf)

    def _init_display(self):
        try:
            self._send_command(0x33)
            time.sleep(0.005)
            self._send_command(0x32)
            time.sleep(0.005)
            self._send_command(0x28)
            time.sleep(0.005)
            self._send_command(0x0C)
            time.sleep(0.005)
            self._send_command(0x01)
            self.BUS.write_byte(self.LCD_ADDR, 0x08)
        except Exception:
            raise Exception("Failed to initialize display")

    def clear(self):
        self._send_command(0x01)

    def open_light(self):
        self.BUS.write_byte(0x27, 0x08)
        self.BUS.close()

    def write(self, x, y, text):
        if x < 0:
            x = 0
        if x > 19:
            x = 19
        if y < 0:
            y = 0
        if y > 3:
            y = 3
        self.lcd_lines[y] = text
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        addr = 0x80 + row_offsets[y] + x
        self._send_command(addr)

        for chr in text:
            self._send_data(ord(chr))

    def get_max_characters(self):
        # Returns the maximum number of characters per line for the display.
        return 20

    def set_cursor_position(self, col, row):
        if col < 0 or col >= 20:
            raise ValueError("col must be between 0 and 19")
        if row < 0 or row >= 4:
            raise ValueError("row must be between 0 and 3")
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        addr = 0x80 + row_offsets[row] + col
        self._send_command(addr)

    def scroll_text(self, line_number, text, direction="left", delay=0.3):
        if line_number < 0 or line_number >= 4:
            raise ValueError("line_number must be between 0 and 3")
        if direction not in ["left", "right"]:
            raise ValueError("direction must be 'left' or 'right'")

        self.clear_line(line_number)
        if direction == "left":
            for i in range(len(text) + 20):
                display_text = text[i:i + 20]
                self.set_cursor_position(0, line_number)
                self.write(0, line_number, display_text.ljust(20))
                time.sleep(delay)
        elif direction == "right":
            for i in range(len(text) + 20):
                display_text = text[max(0, len(text) - 20 - i):len(text) - i]
                self.set_cursor_position(0, line_number)
                self.write(0, line_number, display_text.rjust(20))
                time.sleep(delay)

    def clear_line(self, line_number):
        if line_number < 0 or line_number >= 4:
            raise ValueError("line_number must be between 0 and 3")
        self.set_cursor_position(0, line_number)
        self.write(0, line_number, " " * 20)

    def display_default_four_rows(self):
        self.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."], justification='left')

    def display_text_with_border(self, texts, full_display_border=False):
        self.clear()
        border_line = '*' * 20

        if full_display_border:
            self.write(0, 0, border_line)
            for i in range(1, 4):
                line_text = texts[i - 1] if i - 1 < len(texts) else ""
                self.write(0, i, "*" + line_text.center(18) + "*")
            self.write(0, 3, border_line)
        else:
            for i, text in enumerate(texts):
                if i == 0:
                    self.write(0, 0, border_line)
                    self.write(0, 1, "*" + text.center(18) + "*")
                    self.write(0, 2, border_line)
                elif i == 1:
                    self.write(0, 1, border_line)
                    self.write(0, 2, "*" + text.center(18) + "*")
                    self.write(0, 3, border_line)

    def display_four_rows_center(self, texts, justification='center'):
        self.clear()
        num_lines = min(4, len(texts))
        max_chars = 20  # Assuming the display has 20 columns
        for i in range(num_lines):
            text = texts[i]
            self.lcd_lines[i] = text
            if justification == 'left':
                display_text = text.ljust(max_chars)
            elif justification == 'right':
                display_text = text.rjust(max_chars)
            else:  # default to center
                display_text = text.center(max_chars)

            self.write(0, i, display_text)

    def update_line(self, line_number, text, justification='center'):
        if line_number < 0 or line_number >= 4:
            raise ValueError("line_number must be between 0 and 3")

        self.lcd_lines[line_number] = text
        self.display_four_rows_center(self.lcd_lines, justification)
