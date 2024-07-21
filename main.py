# main.py

import time
import board
import busio
from logger import Logger as Log
from display import SSD1308Display
from sensor import Sensor

    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Example of accessing configuration values
        self.server = self.config['DEFAULT'].get('server')
        self.port = self.config['DEFAULT'].getint('port')
        self.username = self.config['DEFAULT'].get('username')
        self.password = self.config['DEFAULT'].get('password')

    def display_config(self):
        print(f"Server: {self.server}")
        print(f"Port: {self.port}")
        print(f"Username: {self.username}")
        print(f"Password: {self.password}")

    def update_config(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
            
            
def main():
    # Initialize I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # Create an instance of the SSD1308Display class
    display = SSD1308Display(128, 64, i2c)

    # Display centered text
    display.display_initializing("Initializing...")
    time.sleep(5)

    # Display centered text
    display.display_centered_text("Hello, World!")
    time.sleep(5)

    sht30_sensor = Sensor('SHT30', 0x44)
    sht41_sensor = Sensor('SHT41', 0x44)
    start_time = time.time()
    print(start_time)

    logger = Log("log.csv")

    while True:
        current_time = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # Read and print sensor data every 10 seconds
        if int(current_time - start_time) % 10 == 0:
            sht41_output = sht41_sensor.read_sensor()
            print(sht41_output)

            logger.log(timestamp, 'SHT41', '01',
                       f"Temperature: {sht41_output['temperature']}C, Humidity: {sht41_output['humidity']}%")
            sht30_output = sht30_sensor.read_sensor()
            logger.log(timestamp, 'SHT30', '02',
                       f"Temperature: {sht30_output['temperature']}C, Humidity: {sht30_output['humidity']}%")

            print("SHT41 Sensor Reading:", sht41_output)
            print("SHT30 Sensor Reading:", sht30_output)
            display.display_centered_text(f"SHT41 - {sht41_output['temperature']}°C")

        # Heat the sensors every 30 seconds
        if int(current_time - start_time) % 30 == 0:
            print("Heating SHT41 sensor...")
            sht41_sensor.heat_sensor()
            logger.log(timestamp, 'SHT41', '01', "Heating SHT41 sensor...")

            print("Heating SHT30 sensor...")
            sht30_sensor.heat_sensor()
            logger.log(timestamp, 'SHT30', '02', "Heating SHT30 sensor...")

        # Sleep for a short duration to avoid multiple reads/heats within the same second
        time.sleep(0.1)


if __name__ == "__main__":
    main()
