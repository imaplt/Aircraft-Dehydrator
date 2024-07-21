import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import time

def main():
    # Initialize I2C interface
    i2c = busio.I2C(board.SCL, board.SDA)

    # Initialize SSD1306 display
    WIDTH = 128
    HEIGHT = 64
    oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

    # Create a blank image for drawing
    image = Image.new("1", (WIDTH, HEIGHT))

    # Get drawing object to draw on image
    draw = ImageDraw.Draw(image)

    # Load the Arial font and draw text with increasing font sizes
    y_position = 0
    for font_size in range(8, 32, 2):
        try:
            font = ImageFont.truetype("Quicksand-Medium.ttf", font_size)  # Adjust path if necessary
        except IOError:
            print(f"Font file not found for size {font_size}.")
            continue

        text = f"Size {font_size}"
        text_width, text_height = draw.textsize(text, font=font)
        text_x = (WIDTH - text_width) // 2

        # Ensure we don't draw outside the display boundaries
        if y_position + text_height > HEIGHT:
            break

        draw.text((text_x, y_position), text, font=font, fill=1)
        y_position += text_height

        # Display image
        oled.image(image)
        oled.show()

        time.sleep(3)

        oled.fill(0)
        oled.show()


if __name__ == "__main__":
    main()