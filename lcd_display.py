import time
import board
import busio
import bitbangio
from adafruit_character_lcd.character_lcd_i2c import Character_LCD_I2C


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


class LCD2004Display:
    def __init__(self, config_manager, i2c_address=0x27, i2c_type='busio'):
        self.config_manager = config_manager

        # Initialize I2C interface based on i2c_type.
        if i2c_type == 'bitbangio':
            self.i2c = bitbangio.I2C(board.SCL, board.SDA)
        else:
            self.i2c = busio.I2C(board.SCL, board.SDA)

        # Define LCD column and row size for 20x4 LCD.
        self.lcd_columns = 20
        self.lcd_rows = 4

        # Initialize the LCD class using I2C
        self.lcd = Character_LCD_I2C(self.i2c, i2c_address, self.lcd_columns, self.lcd_rows)

        # Initialize lines
        self.lines = [""] * 4

    def reset_screen(self):
        self.lcd.clear()
        self.lines = [""] * 4

    def clear_screen(self):
        self.lcd.clear()

    def set_font(self, font_path=None, font_size=10):
        # The LCD2004 is a character display and does not support custom fonts in the same way as graphical displays.
        pass

    def get_max_characters(self):
        return self.lcd_columns

    def display_text_center(self, text):
        self.clear_screen()
        centered_text = text.center(self.lcd_columns)
        self.lcd.message = centered_text

    def display_four_rows_center(self, texts):
        self.clear_screen()
        self.lines = [""] * 4  # Reset lines
        for i in range(min(4, len(texts))):
            self.lines[i] = texts[i]
            centered_text = texts[i].center(self.lcd_columns)
            self.lcd.cursor_position(0, i)
            self.lcd.message = centered_text

    def update_line(self, line_number, text):
        if line_number < 0 or line_number >= 4:
            raise ValueError("line_number must be between 0 and 3")

        self.lines[line_number] = text
        centered_text = text.center(self.lcd_columns)
        self.lcd.cursor_position(0, line_number)
        self.lcd.message = centered_text

    def display_text_center_with_border(self, text):
        self.clear_screen()
        border_line = '*' * self.lcd_columns
        self.lcd.message = border_line + "\n"
        centered_text = text.center(self.lcd_columns)
        self.lcd.message += centered_text + "\n"
        self.lcd.message += border_line


if __name__ == "__main__":

    config_manager = ConfigManager(font_path='path/to/font.ttf', font_size=12, border_size=2)
    display = LCD2004Display(config_manager)
    print("Max characters per line:", display.get_max_characters())
    display.display_text_center("Hello World!")
    time.sleep(2)
    display.display_four_rows_center(["Line 1", "Line 2", "Line 3", "Line 4"])
    time.sleep(2)
    display.display_text_center_with_border("Border Text")
    time.sleep(2)
    display.update_line(2, "Updated Line 3")
