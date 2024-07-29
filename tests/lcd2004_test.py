#!/usr/bin/env python3
import LCD2004
import time


def display_text_center_with_border(self, text):
    LCD2004.clear()
    border_line = '*' * self.lcd_columns
    LCD2004.write(0, 0, border_line)
    centered_text = text.center(self.lcd_columns)
    LCD2004.write(0, 1, centered_text)
    LCD2004.write(0, 2, border_line)


def display_four_rows_center(self, texts):
    LCD2004.clear()
    self.lines = [""] * self.lcd_rows  # Reset lines
    for i in range(min(self.lcd_rows, len(texts))):
        self.lines[i] = texts[i]
        centered_text = texts[i].center(self.lcd_columns)
        self.write(0, i, centered_text)


def display_default_four_rows(self):
    display_four_rows_center(["Internal:", "reading...", "External:", "reading..."])


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


def setup():
    LCD2004.init(0x27, 1)  # init(slave address, background light)
    LCD2004.write(0, 0, 'Hello, world')
    LCD2004.write(0, 1, 'IIC/I2C LCD2004')
    LCD2004.write(5, 2, '20 cols, 4 rows')
    LCD2004.write(0, 3, 'www.sunfounder.com')
    time.sleep(2)
    display_default_four_rows()
    time.sleep(2)
    update_line(2, 'Hello, world')


def destroy():
    LCD2004.clear()




if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        destroy()
