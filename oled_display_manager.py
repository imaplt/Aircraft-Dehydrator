from PIL import Image, ImageDraw
from enum import Enum
from display import COLORS

def set_brightness(color_name, brightness_factor):
    """ Adjust brightness of the named color. """
    if color_name not in COLORS:
        raise ValueError(f"Color '{color_name}' not found!")

    color = COLORS[color_name]
    return tuple(int(c * brightness_factor) for c in color)

def splash_screen(self, text):
    color_name = "white"
    brightness_factor = 1.0
    # Get color with brightness applied
    color = set_brightness(color_name, brightness_factor)
    border_size = self.config_manager.get_border_size()
    bbox = self.draw.textbbox((0, 0), text, font=self.font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x_position = (self.width - text_width) // 2
    position = (x_position, (self.height - text_height) // 2)
    self.draw.rectangle((0, 0, self.width, self.height), fill="black")  # Clear the screen
    # Draw border
    self.draw.rectangle((border_size, border_size, self.width - border_size - 1, self.height - border_size - 1),
                        outline=color, fill=0)
    self.draw.text(position, text, font=self.font, fill=color)

def display_rows(self, texts, color_name="white",
                        brightness_factor=1.0, justification='center'):
    num_lines = min(5, len(texts))
    line_height = self.height // num_lines

    # Get color with brightness applied
    color = set_brightness(color_name, brightness_factor)

    for i in range(num_lines):
        text = texts[i]
        self.oled_lines[i] = text
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate horizontal position based on justification
        if justification == 'left':
            x_position = 0
        elif justification == 'right':
            x_position = self.width - text_width
        else:  # default to center
            x_position = (self.width - text_width) // 2

        position = (x_position, i * line_height + (line_height - text_height) // 2)
        self.draw.text(position, text, font=self.font, fill=color)

class Screen(Enum):
    DEFAULT = (0, "Internal Sensor Screen")
    FAN = (1, "Fan Status Screen")
    INTERNAL = (2, "Internal Stats Screen")
    AMBIENT = (3, "Ambient Stats")
    HUMIDITY = (4, "Humidity Set Screen")
    FAN_LIMIT = (5, "Fan Limit")
    SHUTDOWN = (6, "Shutdown")
    INITIAL = (7, "Initial")

    def __init__(self, index, title):
        self.index = index                  # The screen index (for switching)
        self.title = title                  # The screen title


class OLEDDisplayManager:
    def __init__(self,configuration, width, height, font):
        self.config_manager = configuration
        self.width = width
        self.height = height
        self.font = font

        # Initialize 8 different image buffers for the OLED
        self.images = [Image.new('RGB', (self.width, self.height), "black") for _ in range(8)]

        # Initialize a list of drawing objects for each image buffer
        self.draws = [ImageDraw.Draw(img) for img in self.images]

        # Current image being displayed (default to the first one)
        self.current_image_index = 0
        self.image = self.images[self.current_image_index]
        self.draw = self.draws[self.current_image_index]

        # Dictionary mapping screen indexes to update methods
        self.screen_update_methods = {
            7: self.initial_screen,
            6: self.shutdown_screen,
            5: self.fan_limit_screen,
        }
        # Initialize lines
        self.oled_lines = [""] * 5

    def switch_image(self, screen):
        """ Switch to a different image by index (0 to 7) """
        index = screen.index
        if 0 <= index < len(self.images):
            self.current_image_index = index
            self.image = self.images[self.current_image_index]
            self.draw = self.draws[self.current_image_index]
            # Call the corresponding update method to refresh the image content
            if index in self.screen_update_methods:
                self.screen_update_methods[index]()
        else:
            raise IndexError("Image index out of range")

    def display_current_image(self, disp):
        """ Display the currently selected image on the OLED """
        disp.image(self.image)

        # Different update methods for each screen, using dynamic variables

    def update_default_screen(self, status_message):
        """ Update logic for screen 0 (e.g., Welcome screen) """
        self.draw.rectangle((0, 0, self.width, self.height), fill="black")  # Clear the screen
        self.draw.text((10, 30), status_message, fill="white")

    def update_internal_screen(self, texts):
        self.current_image_index = Screen.INTERNAL.index
        self.image = self.images[self.current_image_index]
        self.draw = self.draws[self.current_image_index]
        display_rows(self, texts)

    def update_ambient_screen(self, texts):
        self.current_image_index = Screen.INTERNAL.index
        self.image = self.images[self.current_image_index]
        self.draw = self.draws[self.current_image_index]
        display_rows(self, texts)

    def update_fan_screen(self, log_lines):
        """ Update logic for screen 3 (e.g., displaying logs) """
        self.draw.rectangle((0, 0, self.width, self.height), fill="black")  # Clear the screen
        y_pos = 10
        for log in log_lines[:5]:  # Display up to 5 log lines
            self.draw.text((10, y_pos), log, fill="cyan")
            y_pos += 12

    def update_humidity_screen(self, custom_text, color):
        """ Update logic for screen 4 (e.g., custom message screen) """
        self.draw.rectangle((0, 0, self.width, self.height), fill="black")  # Clear the screen
        self.draw.text((10, 30), custom_text, fill=color)

    def initial_screen(self):
        text="Initializing..."
        splash_screen(self,text)

    def shutdown_screen(self):
        text = "Shutting down..."
        splash_screen(self, text)

    def fan_limit_screen(self):
        text = "Fan Limit..."
        splash_screen(self, text)
