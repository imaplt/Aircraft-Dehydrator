import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw

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

# Define the coordinates for the heart shape
heart = [
    (64, 32), (68, 28), (72, 24), (76, 20), (80, 18), (84, 18),
    (88, 20), (92, 24), (96, 28), (100, 32), (96, 36), (92, 40),
    (88, 44), (84, 48), (80, 52), (76, 56), (72, 60), (68, 64),
    (64, 68), (60, 64), (56, 60), (52, 56), (48, 52), (44, 48),
    (40, 44), (36, 40), (32, 36), (28, 32), (32, 28), (36, 24),
    (40, 20), (44, 18), (48, 18), (52, 20), (56, 24), (60, 28)
]

# Draw the heart shape
draw.polygon(heart, outline=1, fill=1)

# Display image
oled.image(image)
oled.show()

# Optional: Save the image to a file for debugging
image.save("heart.bmp")