import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont


class SSD1308Display:
    def __init__(self, width, height, i2c_bus):
        self.width = width
        self.height = height
        self.i2c = i2c_bus
        self.display = adafruit_ssd1306.SSD1306_I2C(width, height, i2c_bus)
        self.display.fill(0)
        self.display.show()

    def display_centered_text(self, text):
        # Create a blank image for drawing.
        image = Image.new('1', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        # Load a font
        font = ImageFont.load_default()

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
