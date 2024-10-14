from PIL import Image, ImageDraw


class OLEDDisplayManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Initialize 5 different image buffers for the OLED
        self.images = [Image.new('RGB', (self.width, self.height), "black") for _ in range(5)]

        # Initialize a list of drawing objects for each image buffer
        self.draws = [ImageDraw.Draw(img) for img in self.images]

        # Current image being displayed (default to the first one)
        self.current_image_index = 0
        self.image = self.images[self.current_image_index]
        self.draw = self.draws[self.current_image_index]


    def switch_image(self, index):
        """ Switch to a different image by index (0 to 4) """
        if 0 <= index < len(self.images):
            self.current_image_index = index
            self.image = self.images[self.current_image_index]
            self.draw = self.draws[self.current_image_index]
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

    def update_internal_screen(self, temperature, humidity):
        """ Update logic for screen 1 (e.g., showing temperature and humidity) """
        self.draw.rectangle((0, 0, self.width, self.height), fill="black")  # Clear the screen
        self.draw.text((10, 20), f"Temp: {temperature}C", fill="green")
        self.draw.text((10, 40), f"Humidity: {humidity}%", fill="green")

    def update_ambient_screen(self, system_status, uptime):
        """ Update logic for screen 2 (e.g., System status) """
        self.draw.rectangle((0, 0, self.width, self.height), fill="black")  # Clear the screen
        self.draw.text((10, 20), f"System: {system_status}", fill="yellow")
        self.draw.text((10, 40), f"Uptime: {uptime}", fill="yellow")

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