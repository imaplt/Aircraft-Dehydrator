#!/usr/bin/env python3
import time
import smbus2 as smbus


class LCD2004Display:
    def __init__(self, configuration, addr=0x27, bl=1):
        self.BUS = smbus.SMBus(1)
        self.LCD_ADDR = addr
        self.BLEN = bl
        self._init_display()
        # Initialize lines
        self.lines = [""] * 4

        # self.i2c_address = i2c_address
        self.config_manager = configuration
        #
        # # Initialize I2C interface based on i2c_type.
        # if i2c_type == 'bitbangio':
        #     self.i2c = bitbangio.I2C(board.D27, board.D22)
        # else:
        #     self.i2c = busio.I2C(board.SCL, board.SDA)

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

    def display_text_with_border(self, text_lines, full_display_border=False):
        self.clear()
        border_line = '*' * 20

        if full_display_border:
            self.write(0, 0, border_line)
            for i in range(1, 4):
                line_text = text_lines[i - 1] if i - 1 < len(text_lines) else ""
                self.write(0, i, "*" + line_text.center(18) + "*")
            self.write(0, 3, border_line)
        else:
            for i, text in enumerate(text_lines):
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

        self.lines[line_number] = text
        self.display_four_rows_center(self.lines, justification)


# Example usage
if __name__ == '__main__':
    display = LCD2004Display(0x27, 1)
    display.write(0, 0, "Hello, World!")
    display.write(0, 1, "I2C 2004 LCD")
    display.write(0, 2, "Line 3")
    display.write(0, 3, "Line 4")

    time.sleep(3)
    display.update_line(2, "Updated Text")
    time.sleep(3)
    display.clear()
    display.display_default_four_rows()
    time.sleep(3)
    display.clear()

    display.set_cursor_position(10, 2)
    display.write(0, 0, "Set cursor test")
    time.sleep(3)

    display.clear()
    display.scroll_text(0, "Scrolling text left to right", direction="left")
    time.sleep(3)

    display.clear()
    display.scroll_text(0, "Scrolling text right to left", direction="right")
    time.sleep(3)

    display.clear()
    display.display_text_with_border(["Border test"])
    time.sleep(3)

    display.clear()
    display.display_text_with_border(["Full display", "border test"], full_display_border=True)
    time.sleep(3)
