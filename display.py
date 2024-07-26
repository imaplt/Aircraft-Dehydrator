import board
import busio
import adafruit_bitbangio as bitbangio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from adafruit_character_lcd.character_lcd_i2c import Character_LCD_I2C


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
        self.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."], justification='left')

    def display_four_rows_center(self, texts, justification='center'):
        self.clear_screen()
        num_lines = min(4, len(texts))
        self.lines = [""] * 4  # Reset lines
        line_height = self.height // num_lines
        for i in range(num_lines):
            text = texts[i]
            self.lines[i] = text
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

        self.lines[line_number] = text

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
    def __init__(self, i2c_type='bitbangio', i2c_address=0x27):
        self.i2c_address = i2c_address

        # Initialize I2C interface based on i2c_type.
        if i2c_type == 'bitbangio':
            self.i2c = bitbangio.I2C(board.D27, board.D22)
        else:
            self.i2c = busio.I2C(board.SCL, board.SDA)

        # Initialize display.
        self.lcd = Character_LCD_I2C(self.i2c, self.i2c_address, 20, 4)

        # Initialize lines
        self.lines = [""] * 4

    def reset_screen(self):
        self.lcd.clear()

    def clear_screen(self):
        self.lcd.clear()

    def set_font(self, font_path=None, font_size=10):
        # Not applicable for Character_LCD_I2C, but kept for interface consistency.
        pass

    def get_max_characters(self):
        # Returns the maximum number of characters per line for the display.
        return 20

    # The justification parameter can be 'left', 'right', or 'center' (default).
    def display_text_center(self, text, justification='center'):
        self.clear_screen()
        max_chars = self.get_max_characters()

        if justification == 'left':
            display_text = text.ljust(max_chars)
        elif justification == 'right':
            display_text = text.rjust(max_chars)
        else:  # default to center
            display_text = text.center(max_chars)

        self.lcd.message = display_text

    def display_default_four_rows(self):
        self.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."], justification='left')

    def display_four_rows_center(self, texts, justification='center'):
        self.clear_screen()
        num_lines = min(4, len(texts))
        self.lines = [""] * 4  # Reset lines

        for i in range(num_lines):
            text = texts[i]
            self.lines[i] = text
            max_chars = self.get_max_characters()

            if justification == 'left':
                display_text = text.ljust(max_chars)
            elif justification == 'right':
                display_text = text.rjust(max_chars)
            else:  # default to center
                display_text = text.center(max_chars)

            self.lcd.message += display_text + "\n"

    def update_line(self, line_number, text, justification='center'):
        if line_number < 0 or line_number >= 4:
            raise ValueError("line_number must be between 0 and 3")

        self.lines[line_number] = text
        self.display_four_rows_center(self.lines, justification)

    def display_text_center_with_border(self, text):
        # Borders are not applicable for Character_LCD_I2C, but kept for interface consistency.
        self.display_text_center(text)
