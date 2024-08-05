import board
import busio
import time
import smbus2 as smbus
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
        self.oled_lines = [""] * 4  # Reset lines
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
        except:
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
