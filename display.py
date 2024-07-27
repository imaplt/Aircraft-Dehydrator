import board
import busio
import time
import smbus2 as smbus
import subprocess
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
    def __init__(self):
        # Note you need to change the bus number to 0 if running on a revision 1 Raspberry Pi.
        self.bus = smbus.SMBus(1)
        self.BLEN = 1  # turn on/off background light
        self.PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
        self.PCF8574A_address = 0x3f  # I2C address of the PCF8574A chip.
        self.LCD_ADDR = self.PCF8574_address
        self.lcd_columns = 20
        self.lcd_rows = 4
        self.lines = [""] * self.lcd_rows

    def write_word(self, addr, data):
        temp = data
        if self.BLEN == 1:
            temp |= 0x08
        else:
            temp &= 0xF7
        self.bus.write_byte(addr, temp)

    def send_command(self, comm):
        # Send bit7-4 firstly
        buf = comm & 0xF0
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self.write_word(self.LCD_ADDR, buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.write_word(self.LCD_ADDR, buf)
        # Send bit3-0 secondly
        buf = (comm & 0x0F) << 4
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self.write_word(self.LCD_ADDR, buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.write_word(self.LCD_ADDR, buf)

    def send_data(self, data):
        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self.write_word(self.LCD_ADDR, buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.write_word(self.LCD_ADDR, buf)
        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self.write_word(self.LCD_ADDR, buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.write_word(self.LCD_ADDR, buf)

    def i2c_scan(self):
        cmd = "i2cdetect -y 1 |awk \'NR>1 {$1=\"\";print}\'"
        result = subprocess.check_output(cmd, shell=True).decode()
        result = result.replace("\n", "").replace(" --", "")
        i2c_list = result.split(' ')
        return i2c_list

    def init_lcd(self, addr=None, bl=1):
        i2c_list = self.i2c_scan()
        if addr is None:
            if '27' in i2c_list:
                self.LCD_ADDR = self.PCF8574_address
            elif '3f' in i2c_list:
                self.LCD_ADDR = self.PCF8574A_address
            else:
                raise IOError("I2C address 0x27 or 0x3f not found.")
        else:
            self.LCD_ADDR = addr
            if str(hex(addr)).strip('0x') not in i2c_list:
                raise IOError(f"I2C address {str(hex(addr))} not found.")
        self.BLEN = bl
        try:
            self.send_command(0x33)  # Must initialize to 8-line mode at first
            time.sleep(0.005)
            self.send_command(0x32)  # Then initialize to 4-line mode
            time.sleep(0.005)
            self.send_command(0x28)  # 2 Lines & 5*7 dots
            time.sleep(0.005)
            self.send_command(0x0C)  # Enable display without cursor
            time.sleep(0.005)
            self.send_command(0x01)  # Clear Screen
            self.bus.write_byte(self.LCD_ADDR, 0x08)
        except:
            return False
        else:
            return True

    def clear(self):
        self.send_command(0x01)  # Clear Screen

    def openlight(self):  # Enable the backlight
        self.bus.write_byte(self.LCD_ADDR, 0x08)
        self.bus.close()

    def write(self, x, y, str):
        if x < 0:
            x = 0
        if x > self.lcd_columns - 1:
            x = self.lcd_columns - 1
        if y < 0:
            y = 0
        if y > self.lcd_rows - 1:
            y = self.lcd_rows - 1
        # Move cursor
        addr = 0x80 + 0x40 * y + x
        self.send_command(addr)
        for chr in str:
            self.send_data(ord(chr))

    def display_num(self, x, y, num):
        addr = 0x80 + 0x40 * y + x
        self.send_command(addr)
        self.send_data(num)

    # New Methods

    def display_four_rows_center(self, texts):
        self.clear()
        self.lines = [""] * self.lcd_rows  # Reset lines
        for i in range(min(self.lcd_rows, len(texts))):
            self.lines[i] = texts[i]
            centered_text = texts[i].center(self.lcd_columns)
            self.write(0, i, centered_text)

    def display_text_center_with_border(self, text):
        self.clear()
        border_line = '*' * self.lcd_columns
        self.write(0, 0, border_line)
        centered_text = text.center(self.lcd_columns)
        self.write(0, 1, centered_text)
        self.write(0, 2, border_line)

    def clear_screen(self):
        self.clear()

    def display_default_four_rows(self):
        self.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."])

    def update_line(self, line_number, text, justification='center'):
        if line_number < 0 or line_number >= self.lcd_rows:
            raise ValueError("line_number must be between 0 and 3")

        self.lines[line_number] = text
        max_chars = self.lcd_columns

        if justification == 'left':
            display_text = text.ljust(max_chars)
        elif justification == 'right':
            display_text = text.rjust(max_chars)
        else:  # default to center
            display_text = text.center(max_chars)
        self.write(0, line_number, display_text)
