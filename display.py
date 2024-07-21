import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import board
import busio


class SSD1308Display:
    def __init__(self, width, height, i2c_bus):
        self.width = width
        self.height = height
        self.i2c = i2c_bus
        self.display = adafruit_ssd1306.SSD1306_I2C(width, height, i2c_bus)
        self.display.fill(0)
        self.display.show()
        self.border = 5
        self.font = "Quicksand-Regular.ttf"
        self.med_font = "Quicksand-Medium.ttf"
        self.light_font = "Quicksand-Light.ttf"
        self.bold_font = "Quicksand-Bold.ttf"

    def display_initializing(self, text):
        # Initialize I2C interface
        i2c = busio.I2C(board.SCL, board.SDA)

        image = Image.new('1', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        i2c = board.I2C()
        oled = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, i2c, addr=0x3C)
        # Clear display.
        oled.fill(0)
        oled.show()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        image = Image.new("1", (oled.width, oled.height))

        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)

        # Draw a white background
        draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=255)

        # Draw a smaller inner rectangle
        draw.rectangle(
            (self.border, self.border, oled.width - self.border - 1, oled.height - self.border - 1),
            outline=0,
            fill=0,
        )

        # Load a larger font
        font_size = 20
        font = ImageFont.truetype(self.font, font_size)  # You can use any .ttf font available

        # Draw Some Text
        bbox = font.getbbox(text)
        (font_width, font_height) = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (oled.width // 2 - font_width // 2, oled.height // 2 - font_height // 2), text,
            font=font, fill=255,
        )

        # Display image
        self.display.image(image)
        self.display.show()

    def display_centered_text(self, text):
        # Create a blank image for drawing.
        image = Image.new('1', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        # Load a larger font
        font_size = 18
        font = ImageFont.truetype(self.font, font_size)  # You can use any .ttf font available

        # Calculate width and height of the text to be displayed
        text_width = draw.textlength(text, font=font)
        text_height = 1
        # Calculate position for centered text
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2

        # Draw the text
        draw.text((x, y), text, font=font, fill=255)

        # Display image
        self.display.image(image)
        self.display.show()
