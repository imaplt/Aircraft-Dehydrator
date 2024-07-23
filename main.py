# main.py

import time
from logger import Logger as Log
from display import SSD1306Display, DisplayConfig
from sensor import Sensor
from config_manager import ConfigManager


class MyDehydrator:

    def __init__(self, configuration):
        self.config_manager = configuration
        self.logger = Log
        self.logfile = self.config_manager.get_config('logfile')
        self.minimum = self.config_manager.get_int_config('minimum')
        self.maximum = self.config_manager.get_int_config('maximum')
        self.fontsize = self.config_manager.get_int_config('fontsize')
        self.font = self.config_manager.get_config('font')
        self.max_log_size = self.config_manager.get_int_config('max_log_size')
        self.max_archive_size = self.config_manager.get_int_config('max_archive_size')


if __name__ == "__main__":

    # Initialize lines
    lines = [""] * 4  # For four line display...
    config_manager = ConfigManager('config.ini')
    module = MyDehydrator(config_manager)
    # config_manager.display_config()
    # Update configuration
    # config_manager.update_config('CUSTOM', 'minimum', '21')
    # config_manager.update_config('CUSTOM', 'maximum', '35')
    # Example usage:

    display_config = DisplayConfig(font_path='Quicksand-Regular.ttf', font_size=16, border_size=5)
    display = SSD1306Display(display_config)
    print("Max characters per line:", display.get_max_characters())

    # Display centered text
    display.display_text_center("Initializing...")
    time.sleep(3)

    sht30_sensor = Sensor('SHT30', 0x44)
    sht41_sensor = Sensor('SHT41', 0x44)

    logger = Log(module.logfile, module.max_log_size, module.max_archive_size)

    # Initialize previous output values to None
    sht30_previous_output = {'temperature': 0, 'humidity': 0}
    sht41_previous_output = {'temperature': 0, 'humidity': 0}
    print("SHT41 Mode: ", sht41_sensor.sensor_mode())
    print("SHT30 Mode: ", sht41_sensor.sensor_mode())

    display.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."])
    time.sleep(2)
    start_time = time.time()
    while True:
        current_time = time.time()

        # Read and print sensor data every 10 seconds
        if int(current_time - start_time) % 10 == 0:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            sht41_output = sht41_sensor.read_sensor()
            if (abs(sht41_output['temperature'] - sht41_previous_output['temperature']) > 0.1 or
                    abs(sht41_output['humidity'] - sht41_previous_output['humidity']) > 0.3):
                logger.log(timestamp, 'SHT41', '01',
                           f"Temperature: {sht41_output['temperature']}C, Humidity: {sht41_output['humidity']}%")
                # Update previous output values
                sht41_previous_output['temperature'] = sht41_output['temperature']
                sht41_previous_output['humidity'] = sht41_output['humidity']
                print("SHT41 Sensor Reading:", sht41_output)
                display.update_line(1,  f"{sht41_output['humidity']}% - {sht41_output['temperature']}°C")
            else:
                print('SHT41 Measurements matched or humidity change is less than 0.3 --> skipping....')

            sht30_output = sht30_sensor.read_sensor()
            if (abs(sht30_output['temperature'] - sht30_previous_output['temperature']) > 0.1 or
                    abs(sht30_output['humidity'] - sht30_previous_output['humidity']) > 0.3):
                logger.log(timestamp, 'SHT30', '02',
                           f"Temperature: {sht30_output['temperature']}C, Humidity: {sht30_output['humidity']}%")
                # Update previous output values
                sht30_previous_output['temperature'] = sht30_output['temperature']
                sht30_previous_output['humidity'] = sht30_output['humidity']
                print("SHT30 Sensor Reading:", sht30_output)
                display.update_line(3, f"{sht30_output['humidity']}% - {sht30_output['temperature']}°C")
            else:
                print('SHT30 Measurements matched or humidity change is less than 0.3 --> skipping....')

        # Heat the sensors every 90 seconds
        if int(current_time - start_time) % 90 == 0:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print("Heating SHT41 sensor...")
            sht41_sensor.heat_sensor()
            logger.log(timestamp, 'SHT41', '01', "Heating SHT41 sensor...")

            print("Heating SHT30 sensor...")
            sht30_sensor.heat_sensor()
            logger.log(timestamp, 'SHT30', '02', "Heating SHT30 sensor...")

        # Sleep for a short duration to avoid multiple reads/heats within the same second
        time.sleep(0.5)
