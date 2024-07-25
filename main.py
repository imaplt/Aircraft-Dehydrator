# main.py

import time
from datetime import timedelta
from humidity_controller import HumidityController
from logger import Logger as Log
from display import SSD1306Display, DisplayConfig
from sensor import Sensor
from config_manager import ConfigManager


class MyDehydrator:

    def __init__(self, configuration):
        self.config_manager = configuration
        self.logger = Log
        self.logfile = self.config_manager.get_config('logfile')
        self.min_humidity = self.config_manager.get_int_config('min_humidity')
        self.max_humidity = self.config_manager.get_int_config('max_humidity')
        self.font = self.config_manager.get_config('font')
        self.fontsize = self.config_manager.get_int_config('fontsize')
        self.border = self.config_manager.get_int_config('border')
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
 
    display_config = DisplayConfig(font_path=module.font, font_size=module.fontsize, border_size=module.border)
    display = SSD1306Display(display_config)
    # print("Max characters per line:", display.get_max_characters())

    # Display centered text
    display.display_text_center("Initializing...")
    time.sleep(3)

    internalsensor = Sensor('SHT41', 0x44)
    externalsensor = Sensor('SHT30', 0x44)

    logger = module.logger(module.logfile, module.max_log_size, module.max_archive_size)

    # Initialize previous output values to None
    internalprevious_output = {'temperature': 0, 'humidity': 0}
    externalprevious_output = {'temperature': 0, 'humidity': 0}
    print("External Mode: ", externalsensor.sensor_mode())
    print("Internal Mode: ", internalsensor.sensor_mode())

    display.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."], justification='left')
    time.sleep(2)
    start_time = time.time()
    controller = HumidityController()

    while True:
        current_time = time.time()

        # Read and print sensor data every 2 seconds
        if int(current_time - start_time) % 1 == 0:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            externaloutput = externalsensor.read_sensor()
            if abs(externaloutput['humidity'] - externalprevious_output['humidity']) > 0.2:
                logger.log(timestamp, 'External', '01',
                           f"Temperature: {externaloutput['temperature']}C, Humidity: {externaloutput['humidity']}%")
                # Update previous output values
                externalprevious_output['temperature'] = externaloutput['temperature']
                externalprevious_output['humidity'] = externaloutput['humidity']
                print("External Sensor Reading:", externaloutput)
                display.update_line(3, justification='left',
                                    text=f"{externaloutput['humidity']}% - {externaloutput['temperature']}°C")
            # else:
                # print('External Measurements matched or humidity change is less than 0.3 --> skipping....')

            time.sleep(.1)
            internaloutput = internalsensor.read_sensor()
            if abs(internaloutput['humidity'] - internalprevious_output['humidity']) > 0.2:
                logger.log(timestamp, 'Internal', '02',
                           f"Temperature: {internaloutput['temperature']}C, Humidity: {internaloutput['humidity']}%")
                # Update previous output values
                internalprevious_output['temperature'] = internaloutput['temperature']
                internalprevious_output['humidity'] = internaloutput['humidity']
                print("Internal Sensor Reading:", internaloutput)
                display.update_line(1, justification='left',
                                    text=f"{internaloutput['humidity']}% - {internaloutput['temperature']}°C")
                print(internaloutput['humidity'], module.max_humidity)
                if internaloutput['humidity'] > module.max_humidity:
                    started = controller.engage_fan(controller)
                    if started:
                        logger.log(timestamp, 'Fan', '',
                                   f"Fan started, exceeded MAX humidity of: {internaloutput['humidity']}%")
                        print(f"Fan started, exceeded set humidity of: {internaloutput['humidity']}%")
                elif internaloutput['humidity'] < module.min_humidity:
                    stopped, run_time = controller.disengage_fan(controller)
                    if stopped:
                        print("Fan stopped...")
                        logger.log(timestamp, 'Fan', '', f"Fan stopped, passed MIN humidity of: {internaloutput['humidity']}%")
                        logger.log(timestamp, 'Fan', '', f"Fan run time: { str(timedelta(seconds=run_time))}")
                # else:
                    # print('Internal Measurements matched or humidity change is less than 0.3 --> skipping....')

            time.sleep(.1)  # Adjust as needed

            # Example logging for fan status
            # status, rpm = self.fan_status()
            # logging.info(f"Fan status: {status}, RPM: {rpm}")

        # Heat the sensors every 90 seconds
        if int(current_time - start_time) % 90 == 0:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print("Heating External sensor...")
            externalsensor.heat_sensor()
            logger.log(timestamp, 'External', '01', "Heating External sensor...")

            print("Heating Internal sensor...")
            internalsensor.heat_sensor()
            logger.log(timestamp, 'Internal', '02', "Heating Internal sensor...")

        # Sleep for a short duration to avoid multiple reads/heats within the same second
        time.sleep(0.5)
