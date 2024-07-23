import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


class DisplayConfig:
    def __init__(self, font_path=None, font_size=10, border_size=1):
        self.font_path = font_path
        self.font_size = font_size
        self.border_size = border_size

    def get_font_path(self):
        return self.font_path

    def get_font_size(self):
        return self.font_size

    def get_border_size(self):
        return self.border_size


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
        self.set_font(self.config_manager.get_font_path(), self.config_manager.get_font_size())

        # Initialize lines
        self.lines = [""] * 4

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

    def display_text_center(self, text):
        self.clear_screen()
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((self.width - text_width) // 2, (self.height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.show()

    def display_four_rows_center(self, texts):
        self.clear_screen()
        num_lines = min(4, len(texts))
        line_height = self.height // num_lines
        for i in range(num_lines):
            text = texts[i]
            bbox = self.draw.textbbox((0, 0), text, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((self.width - text_width) // 2, i * line_height + (line_height - text_height) // 2)
            self.draw.text(position, text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.show()

    def update_line(self, line_number, text):
        if line_number < 0 or line_number >= 4:
            raise ValueError("line_number must be between 0 and 3")
        self.lines[line_number] = text
        self.clear_screen()
        num_lines = 4
        line_height = self.height // num_lines
        for i in range(num_lines):
            text = self.lines[i]
            bbox = self.draw.textbbox((0, 0), text, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((self.width - text_width) // 2, i * line_height + (line_height - text_height) // 2)
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
