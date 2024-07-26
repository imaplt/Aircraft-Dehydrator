import board
import busio
import adafruit_bitbangio as bitbangio
import time
from adafruit_character_lcd.character_lcd_i2c import Character_LCD_I2C


class LCD2004Display:
    def __init__(self, configuration, i2c_type='busio', i2c_address=0x27):
        self.i2c_address = i2c_address
        self.config_manager = configuration

        # Initialize I2C interface based on i2c_type.
        if i2c_type == 'bitbangio':
            self.i2c = bitbangio.I2C(board.D27, board.D22)
        else:
            self.i2c = busio.I2C(board.SCL, board.SDA)

        # Initialize display.
        self.lcd = Character_LCD_I2C(self.i2c, self.i2c_address, 20, 4)
        self.lcd.message("LCD Display")
        # Initialize lines
        self.lines = [""] * 4

    def reset_screen(self):
        self.lcd.clear()

    def clear_screen(self):
        self.lcd.clear()

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


# Example usage
if __name__ == "__main__":
    class MockConfiguration:
        def get_font_path(self):
            return None

        def get_font_size(self):
            return 10

        def get_border_size(self):
            return 1

    config = MockConfiguration()
    lcd_display = LCD2004Display(config)

    lcd_display.display_default_four_rows()
    time.sleep(5)
    # lcd_display.update_line(1, "Updated reading")
    # time.sleep(5)
    # lcd_display.display_text_center("Centered Text")
    # time.sleep(5)
