#!/usr/bin/env python3

import time
import smbus2 as smbus

BUS = smbus.SMBus(1)
LCD_ADDR = 0x27  # Default I2C address
BLEN = 1  # Backlight enabled


def write_word(addr, data):
    global BLEN
    temp = data
    if BLEN == 1:
        temp |= 0x08
    else:
        temp &= 0xF7
    BUS.write_byte(addr, temp)


def send_command(comm):
    buf = comm & 0xF0
    buf |= 0x04
    write_word(LCD_ADDR, buf)
    time.sleep(0.002)
    buf &= 0xFB
    write_word(LCD_ADDR, buf)

    buf = (comm & 0x0F) << 4
    buf |= 0x04
    write_word(LCD_ADDR, buf)
    time.sleep(0.002)
    buf &= 0xFB
    write_word(LCD_ADDR, buf)


def send_data(data):
    buf = data & 0xF0
    buf |= 0x05
    write_word(LCD_ADDR, buf)
    time.sleep(0.002)
    buf &= 0xFB
    write_word(LCD_ADDR, buf)

    buf = (data & 0x0F) << 4
    buf |= 0x05
    write_word(LCD_ADDR, buf)
    time.sleep(0.002)
    buf &= 0xFB
    write_word(LCD_ADDR, buf)


def init(addr, bl):
    global LCD_ADDR
    global BLEN
    LCD_ADDR = addr
    BLEN = bl
    try:
        send_command(0x33)
        time.sleep(0.005)
        send_command(0x32)
        time.sleep(0.005)
        send_command(0x28)
        time.sleep(0.005)
        send_command(0x0C)
        time.sleep(0.005)
        send_command(0x01)
        BUS.write_byte(LCD_ADDR, 0x08)
    except:
        return False
    else:
        return True


def clear():
    send_command(0x01)


def openlight():
    BUS.write_byte(0x27, 0x08)
    BUS.close()


def write(x, y, text):
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
    send_command(addr)

    for chr in text:
        send_data(ord(chr))


def set_cursor_position(col, row):
    if col < 0 or col >= 20:
        raise ValueError("col must be between 0 and 19")
    if row < 0 or row >= 4:
        raise ValueError("row must be between 0 and 3")
    row_offsets = [0x00, 0x40, 0x14, 0x54]
    addr = 0x80 + row_offsets[row] + col
    send_command(addr)


def scroll_text(line_number, text, direction="left", delay=0.3):
    if line_number < 0 or line_number >= 4:
        raise ValueError("line_number must be between 0 and 3")
    if direction not in ["left", "right"]:
        raise ValueError("direction must be 'left' or 'right'")

    clear_line(line_number)
    if direction == "left":
        for i in range(len(text) + 20):
            display_text = text[i:i + 20]
            set_cursor_position(0, line_number)
            write(0, line_number, display_text.ljust(20))
            time.sleep(delay)
    elif direction == "right":
        for i in range(len(text) + 20):
            display_text = text[max(0, len(text) - 20 - i):len(text) - i]
            set_cursor_position(0, line_number)
            write(0, line_number, display_text.rjust(20))
            time.sleep(delay)


def clear_line(line_number):
    if line_number < 0 or line_number >= 4:
        raise ValueError("line_number must be between 0 and 3")
    set_cursor_position(0, line_number)
    write(0, line_number, " " * 20)


def display_text_with_border(text_lines, full_display_border=False):
    clear()
    border_line = '*' * 20

    if full_display_border:
        write(0, 0, border_line)
        for i in range(1, 4):
            line_text = text_lines[i - 1] if i - 1 < len(text_lines) else ""
            write(0, i, "*" + line_text.center(18) + "*")
        write(0, 3, border_line)
    else:
        for i, text in enumerate(text_lines):
            if i == 0:
                write(0, 0, border_line)
                write(0, 1, "*" + text.center(18) + "*")
                write(0, 2, border_line)
            elif i == 1:
                write(0, 1, border_line)
                write(0, 2, "*" + text.center(18) + "*")
                write(0, 3, border_line)


# Example usage
if __name__ == '__main__':
    init(0x27, 1)
    write(0, 0, "Hello, World!")
    write(0, 1, "I2C 2004 LCD")
    write(0, 2, "Line 3")
    write(0, 3, "Line 4")

    time.sleep(3)
    clear()

    set_cursor_position(0, 0)
    write(0, 0, "Set cursor test")
    time.sleep(3)

    clear()
    scroll_text(0, "Scrolling text left to right", direction="left")
    time.sleep(3)

    clear()
    scroll_text(0, "Scrolling text right to left", direction="right")
    time.sleep(3)

    clear()
    display_text_with_border(["Border test"])
    time.sleep(3)

    clear()
    display_text_with_border(["Full display", "border test"], full_display_border=True)
    time.sleep(3)
