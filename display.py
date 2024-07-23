from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306


class ConfigManager:
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
    def __init__(self, config_manager, width=128, height=64, rst=None, i2c_address=0x3C):
        self.width = width
        self.height = height
        self.rst = rst
        self.i2c_address = i2c_address
        self.config_manager = config_manager

        # Initialize display.
        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=self.rst, i2c=self.i2c_address)
        self.disp.begin()

        # Create blank image for drawing.
        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Set the font using config_manager
        self.set_font(self.config_manager.get_font_path(), self.config_manager.get_font_size())

    def reset_screen(self):
        self.disp.clear()
        self.clear_screen()

    def clear_screen(self):
        self.disp.clear()
        self.disp.display()

    def set_font(self, font_path=None, font_size=10):
        if font_path:
            self.font = ImageFont.truetype(font_path, font_size)
        else:
            self.font = ImageFont.load_default()

    def display_text_center(self, text):
        self.clear_screen()
        text_width, text_height = self.draw.textlength(text, font=self.font)
        position = ((self.width - text_width) // 2, (self.height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.display()

    def display_four_rows_center(self, texts):
        self.clear_screen()
        num_lines = min(4, len(texts))
        line_height = self.height // num_lines
        for i in range(num_lines):
            text = texts[i]
            text_width, text_height = self.draw.textlength(text=text, font=self.font)
            position = ((self.width - text_width) // 2, i * line_height + (line_height - text_height) // 2)
            self.draw.text(position, text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.display()

    def display_text_center_with_border(self, text):
        self.clear_screen()
        border_size = self.config_manager.get_border_size()
        self.draw.rectangle((border_size, border_size, self.width - border_size - 1, self.height - border_size - 1),
                            outline=255, fill=0)
        text_width, text_height = self.draw.textlength(text=text, font=self.font)
        position = ((self.width - text_width) // 2, (self.height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.display()


# Example usage:
config_manager = ConfigManager(font_path='path/to/font.ttf', font_size=12, border_size=2)
display = SSD1306Display(config_manager)
display.display_text_center("Hello World!")
display.display_four_rows_center(["Line 1", "Line 2", "Line 3", "Line 4"])
display.display_text_center_with_border("Border Text")
