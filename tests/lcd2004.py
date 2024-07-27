import time
import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_character_lcd.character_lcd_i2c import Character_LCD_I2C

# Configuration
I2C_ADDRESS = 0x27  # Replace with your actual I2C address
LCD_COLUMNS = 20
LCD_ROWS = 4

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the LCD
lcd = Character_LCD_I2C(i2c, I2C_ADDRESS, LCD_COLUMNS, LCD_ROWS)


def test_lcd_display():
    """Test the functionality of the LCD2004 display."""
    print("Testing LCD2004 Display...")

    # Clear the display
    lcd.clear()
    time.sleep(1)

    # Display a message
    message = "Hello, LCD2004!"
    lcd.message = message
    print(f"Displayed message: '{message}'")
    time.sleep(2)

    # Clear the display
    lcd.clear()
    time.sleep(1)

    # Test line by line
    for i in range(LCD_ROWS):
        line_message = f"Line {i + 1}: Test"
        lcd.cursor_position(0, i)  # Move cursor to the beginning of the line
        lcd.message = line_message
        print(f"Displayed message: '{line_message}'")
        time.sleep(2)

    # Test scrolling text
    lcd.clear()
    scrolling_message = "This is a scrolling message! "
    print("Scrolling message...")
    for i in range(len(scrolling_message) + LCD_COLUMNS):
        lcd.cursor_position(0, 0)  # Move cursor to the first line
        lcd.message = scrolling_message[i:i + LCD_COLUMNS]
        time.sleep(0.3)

    # Test clearing display and show border text
    lcd.clear()
    border_line = '*' * LCD_COLUMNS
    lcd.message = border_line + "\nTest Border"
    print(f"Displayed border: '{border_line}' and 'Test Border'")
    time.sleep(3)

    # Final cleanup
    lcd.clear()
    print("Testing complete. Display cleared.")


if __name__ == "__main__":
    try:
        test_lcd_display()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        lcd.clear()
        print("LCD cleared before exiting.")
