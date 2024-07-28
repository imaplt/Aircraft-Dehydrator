import time
import board
import busio
from adafruit_character_lcd.character_lcd_i2c import Character_LCD_I2C


class LCD2004Display:
    def __init__(self, i2c_address=0x27):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.lcd_columns = 20
        self.lcd_rows = 4
        self.lcd = Character_LCD_I2C(self.i2c, self.lcd_columns, self.lcd_rows, i2c_address)
        self.lines = [""] * self.lcd_rows

    def reset_screen(self):
        self.lcd.clear()
        self.lines = [""] * self.lcd_rows

    def clear_screen(self):
        self.lcd.clear()

    def display_text_center(self, text):
        self.clear_screen()
        centered_text = text.center(self.lcd_columns)
        self.lcd.message = centered_text

    def display_four_rows_center(self, texts):
        self.clear_screen()
        for i in range(min(self.lcd_rows, len(texts))):
            self.lines[i] = texts[i]
            centered_text = texts[i].center(self.lcd_columns)
            self.lcd.cursor_position(0, i)
            self.lcd.message = centered_text

    def update_line(self, line_number, text):
        if line_number < 0 or line_number >= self.lcd_rows:
            raise ValueError("line_number must be between 0 and 3")

        self.lines[line_number] = text
        centered_text = text.center(self.lcd_columns)
        self.lcd.cursor_position(0, line_number)
        self.lcd.message = centered_text


def test_lcd2004():
    lcd = LCD2004Display(i2c_address=0x27)
    # Test clear screen
    print("Testing clear_screen...")
    lcd.clear_screen()
    time.sleep(2)

    # Test display text center
    print("Testing display_text_center...")
    lcd.display_text_center("Hello, World!")
    time.sleep(2)

    # Test display four rows center
    print("Testing display_four_rows_center...")
    lcd.display_four_rows_center(["Row 1", "Row 2", "Row 3", "Row 4"])
    time.sleep(2)

    # Test updating specific lines
    print("Testing update_line...")
    lcd.update_line(1, "Updated Row 2")
    time.sleep(2)
    lcd.update_line(3, "Updated Row 4")
    time.sleep(2)

    # Test displaying text with border
    print("Testing display_text_center_with_border...")
    lcd.clear_screen()
    border_line = '*' * lcd.lcd_columns
    lcd.lcd.message = border_line + "\n" + "Centered Text".center(lcd.lcd_columns) + "\n" + border_line
    time.sleep(3)

    # Reset screen at the end
    print("Resetting screen...")
    lcd.reset_screen()


if __name__ == "__main__":
    try:
        test_lcd2004()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Test complete.")
