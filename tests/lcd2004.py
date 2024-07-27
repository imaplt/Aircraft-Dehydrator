#!/usr/bin/env python3
import time
import smbus
import subprocess


class CharLCD2004(object):
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


def loop():
    count = 0
    while True:
        lcd2004.clear_screen()
        lcd2004.display_text_center_with_border("Hello World!")
        time.sleep(2)
        lcd2004.display_four_rows_center(["Counter:", str(count), "Line 3", "Line 4"])
        time.sleep(2)
        lcd2004.update_line(2, "Updated Line 3")
        time.sleep(2)
        lcd2004.display_default_four_rows()
        time.sleep(2)
        count += 1


def destroy():
    lcd2004.clear()


lcd2004 = CharLCD2004()
if __name__ == '__main__':
    print('Program is starting ... ')
    lcd2004.init_lcd(addr=None, bl=1)
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
