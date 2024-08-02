import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

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

# Load a larger font
font_size = 24
font = ImageFont.truetype("Quicksand-Medium.ttf", font_size)  # You can use any .ttf font available

# Define the coordinates for the smaller, centered heart shape
heart = [
    (64, 38), (66, 36), (68, 34), (70, 32), (72, 30), (74, 30),
    (76, 32), (78, 34), (80, 36), (82, 38), (80, 40), (78, 42),
    (76, 44), (74, 46), (72, 48), (70, 50), (68, 52), (66, 54),
    (64, 56), (62, 54), (60, 52), (58, 50), (56, 48), (54, 46),
    (52, 44), (50, 42), (48, 40), (46, 38), (48, 36), (50, 34),
    (52, 32), (54, 30), (56, 30), (58, 32), (60, 34), (62, 36)
]

# Draw the heart shape
draw.polygon(heart, outline=1, fill=1)

# Draw the text 'Love You' at the top of the display
text = "Love You"
text_length = len(text)
# Calculate the position to center the text
text_x = (WIDTH - (text_length * font_size // 2)) // 2
text_y = 0  # Position text at the top of the display
draw.text((text_x, text_y), text, font=font, fill=1)

# Display image
oled.image(image)
oled.show()
