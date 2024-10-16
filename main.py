# main.py

import time
from datetime import timedelta
from gpiozero import Button
from LCD2004 import LCD2004Display
import system_status as SystemStatus
from humidity_controller import HumidityController
from logger import Logger as Log
from display import SSD1306Display, DisplayConfig
from sensor import Sensor
from config_manager import ConfigManager
import sys


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


# Display function placeholders
def display_min_humidity(value):
    print(f"Min Humidity: {value}%")


def display_max_humidity(value):
    print(f"Max Humidity: {value}%")


# Save configuration
def save_config():
    global min_humidity, max_humidity
    print("Saving config...")
    print("Min Humidity: ", min_humidity)
    print("Max Humidity: ", max_humidity)
    config_manager.update_config('min_humidity', min_humidity)
    config_manager.update_config('max_humidity', max_humidity)


def button_pressed_callback(button):
    global min_humidity, max_humidity, last_press_time, humidity_changed, mode

    now = time.time()
    button_name = 'up' if button.pin.number == up_button_pin else 'dn'
    # last_press_time[button_name] = now

    print(f"Button: {button_name} Mode: {mode}")
    print(f"Up last pressed: {last_press_time['up']} DN last pressed: {last_press_time['dn']}")
    print("Humidity Changed: ", humidity_changed)

    if humidity_changed and (now - last_press_time['up'] > 3 and now - last_press_time['dn'] > 3):
        save_config()
        humidity_changed = False
        mode = None

    # Show the current setting when the button is pressed and released
    if mode is None:
        if button_name == 'up':
            print('Up Button Pressed...', mode)
            display_max_humidity(max_humidity)
        else:
            print('DN Button Pressed...')
            display_min_humidity(min_humidity)
    else:
        now = time.time()
        if mode == 'max':
            if button_name == 'up':
                max_humidity += 1
                display_max_humidity(max_humidity)
                humidity_changed = True
                last_press_time['up'] = now
            elif button_name == 'dn':
                max_humidity -= 1
                display_max_humidity(max_humidity)
                humidity_changed = True
                last_press_time['dn'] = now
        elif mode == 'min':
            if button_name == 'up':
                min_humidity += 1
                display_min_humidity(min_humidity)
                humidity_changed = True
                last_press_time['up'] = now
            elif button_name == 'dn':
                min_humidity -= 1
                display_min_humidity(min_humidity)
                humidity_changed = True
                last_press_time['dn'] = now


def button_hold_callback(button):
    global min_humidity, max_humidity, last_press_time, humidity_changed, mode

    button_name = 'up' if button.pin.number == up_button_pin else 'dn'
    last_press_time[button_name] = time.time()
    # print(f"First button: {button_name}")
    # print("Up button held: ", up_button.is_held)
    # print("Dn Button Held: ", dn_button.is_held)
    # print("Up button Is Active: ", up_button.is_active)
    # print("Dn Button IS Active: ", dn_button.is_active)

    if up_button.is_active and dn_button.is_active:
        print("Both buttons are being held...")
        return

    if button_name == 'up':
        print('Up Button Held...')
        display_max_humidity(max_humidity)
        mode = 'max'
    else:
        print('DN Button Held...')
        display_min_humidity(min_humidity)
        mode = 'min'


def cleanup():
    # Test
    # Want to add code here to update display, update log with run time etc
    print('Cleaning Up')
    ssd1306_display.display_text_center_with_border('Shutting down...')
    lcd2004_display.display_text_with_border('Shutting down...')
    logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
               'System', '', "Shutting down...")
    time.sleep(3)
    ssd1306_display.clear_screen()
    lcd2004_display.clear()


def read_installed_devices(config):
    devices = config.get_config('installed_devices').split(',')
    devices = [device.strip() for device in devices]  # Remove any extra whitespace
    return devices


if __name__ == "__main__":
    config_manager = ConfigManager('config.ini')
    module = MyDehydrator(config_manager)
    logger = module.logger(module.logfile, module.max_log_size, module.max_archive_size)
    controller = HumidityController()

    installed_devices = read_installed_devices(config_manager)
    overall_status, statuses = SystemStatus.query_i2c_devices(installed_devices)
    print(f"Overall status: {overall_status}")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for status in statuses:
        print(status)
        logger.log(timestamp, 'System', '', status)
    if overall_status == 'Bad':
        logger.log(timestamp, 'System', 'Overall', "Overall Status: Fail")
        cleanup()
        raise ValueError("Overall Status Failed")
        sys.exit(1)

    # Get initial values
    min_humidity = config_manager.get_int_config('min_humidity')
    max_humidity = config_manager.get_int_config('max_humidity')
    # Get button pins
    up_button_pin = config_manager.get_int_config('up_button_pin')
    dn_button_pin = config_manager.get_int_config('dn_button_pin')

    # GPIO setup using gpiozero
    up_button = Button(up_button_pin, pull_up=True, bounce_time=0.2, hold_time=3)
    dn_button = Button(dn_button_pin, pull_up=True, bounce_time=0.2, hold_time=3)

    # Variables to manage button state and humidity values
    last_press_time = {'up': 0, 'dn': 0}
    button_hold_time = 2
    humidity_changed = False
    mode = None

    # Attach event handlers
    up_button.when_pressed = button_pressed_callback
    up_button.when_held = button_hold_callback

    dn_button.when_pressed = button_pressed_callback
    dn_button.when_held = button_hold_callback

    # Initialize lines
    lines = [""] * 4  # For four line ssd1306_display...

    try:
        ssd1306_display_config = DisplayConfig(font_path=module.font, font_size=module.fontsize,
                                               border_size=module.border)
        ssd1306_display = SSD1306Display(ssd1306_display_config)
        lcd2004_display = LCD2004Display()

        # Display centered text
        ssd1306_display.display_text_center("Initializing...")
        lcd2004_display.display_text_with_border('Initializing...')
        time.sleep(3)

        internalsensor = Sensor('SHT41_Internal', 0x44)
        externalsensor = Sensor('SHT30', 0x44)

        # Initialize previous output values to None
        internalprevious_output = {'temperature': 0, 'humidity': 0}
        externalprevious_output = {'temperature': 0, 'humidity': 0}

        print("External Mode: ", externalsensor.sensor_mode())
        print("Internal Mode: ", internalsensor.sensor_mode())

        ssd1306_display.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."],
                                                 justification='left')
        ssd1306_display.display_default_four_rows()
        time.sleep(2)
        start_time = time.time()
        controller = HumidityController()
        fan_status = controller.fan_status()
        print(fan_status)
        while True:
            current_time = time.time()
            # Read and print sensor data every 2 seconds
            if int(current_time - start_time) % 1 == 0:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                externaloutput = externalsensor.read_sensor()
                if abs(externaloutput['humidity'] - externalprevious_output['humidity']) > 0.2:
                    logger.log(timestamp, 'External', '01',
                               f"Temperature: {externaloutput['temperature']}C,"
                               f" Humidity: {externaloutput['humidity']}%")
                    # Update previous output values
                    externalprevious_output['temperature'] = externaloutput['temperature']
                    externalprevious_output['humidity'] = externaloutput['humidity']
                    print("External Sensor Reading:", externaloutput)
                    ssd1306_display.update_line(
                        3, justification='left',
                        text=f"{externaloutput['humidity']}% - {externaloutput['temperature']}°C")

                time.sleep(.1)
                internaloutput = internalsensor.read_sensor()
                if abs(internaloutput['humidity'] - internalprevious_output['humidity']) > 0.2:
                    logger.log(timestamp, 'Internal', '02',
                               f"Temperature: {internaloutput['temperature']}C,"
                               f" Humidity: {internaloutput['humidity']}%")
                    # Update previous output values
                    internalprevious_output['temperature'] = internaloutput['temperature']
                    internalprevious_output['humidity'] = internaloutput['humidity']
                    print("Internal Sensor Reading:", internaloutput)
                    ssd1306_display.update_line(1,
                                                justification='left', text=f"{internaloutput['humidity']}%"
                                                                           f" - {internaloutput['temperature']}°C")
                    if internaloutput['humidity'] > max_humidity:
                        started = controller.engage_fan()
                        if started:
                            logger.log(timestamp, 'Fan', '',
                                       f"Fan started, exceeded MAX humidity of: {module.max_humidity}%")
                            print(f"Fan started, exceeded set humidity of: {module.max_humidity}%")
                            ssd1306_display.display_text_center_with_border('Fan Started...')
                            time.sleep(1)
                            ssd1306_display.display_default_four_rows()
                    elif internaloutput['humidity'] < min_humidity:
                        stopped, run_time = controller.disengage_fan()
                        if stopped:
                            print("Fan stopped...")
                            logger.log(timestamp, 'Fan', '',
                                       f"Fan stopped, passed MIN humidity of: {module.min_humidity}%")
                            logger.log(timestamp, 'Fan', '', f"Fan run time: {str(timedelta(seconds=run_time))}")
                            ssd1306_display.display_text_center_with_border('Fan Stopped...')
                            time.sleep(1)
                            ssd1306_display.display_default_four_rows()

                time.sleep(.1)  # Adjust as needed
            initial_start = False
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

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected!")

    finally:
        cleanup()
