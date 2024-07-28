# main.py
import time
import threading
from gpiozero import Button
from logger import Logger as Log
from config_manager import ConfigManager


class Buttons:

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
    global last_press_time, button_pressed, mode

    now = time.time()
    button_name = 'up' if button.pin.number == up_button_pin else 'dn'
    print("Mode is: ", mode)

    if button_pressed[button_name]:
        return  # Ignore if button is already pressed

    last_press_time[button_name] = now
    button_pressed[button_name] = True

    # Show the current setting when the button is pressed and released
    if now - last_press_time[button_name] <= button_hold_time:
        if button_name == 'up':
            print('Up Button Pressed...', mode)
            display_max_humidity(max_humidity)
            mode = 'max'
        else:
            print('DN Button Pressed...')
            display_min_humidity(min_humidity)
            mode = 'min'


def button_hold_callback(button):
    global min_humidity, max_humidity, button_pressed, humidity_changed, mode

    button_name = 'up' if button.pin.number == up_button_pin else 'dn'
    button_pressed[button_name] = False

    if button_name == 'up':
        print('Up Button Held...')
        display_max_humidity(max_humidity)
        mode = 'max'
    else:
        print('DN Button Held...')
        display_min_humidity(min_humidity)
        mode = 'min'


def button_hold_check():
    global min_humidity, max_humidity, button_pressed, humidity_changed, mode

    while True:
        now = time.time()
        if mode == 'max':
            if button_pressed['up']:
                max_humidity += 1
                display_max_humidity(max_humidity)
                humidity_changed = True
                last_press_time['up'] = now
            elif button_pressed['dn']:
                max_humidity -= 1
                display_max_humidity(max_humidity)
                humidity_changed = True
                last_press_time['dn'] = now
        elif mode == 'min':
            if button_pressed['up']:
                min_humidity += 1
                display_min_humidity(min_humidity)
                humidity_changed = True
                last_press_time['up'] = now
            elif button_pressed['dn']:
                min_humidity -= 1
                display_min_humidity(min_humidity)
                humidity_changed = True
                last_press_time['dn'] = now

        if humidity_changed and (now - last_press_time['up'] > 3 and now - last_press_time['dn'] > 3):
            save_config()
            humidity_changed = False

        time.sleep(0.1)


def cleanup():
    # Test
    # Want to add code here to update display, update log with run time etc
    print('Cleaning Up')
    logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
               'System', '', "Shutting down...")
    time.sleep(3)


def read_installed_devices(config):
    devices = config.get_config('installed_devices').split(',')
    devices = [device.strip() for device in devices]  # Remove any extra whitespace
    return devices


if __name__ == "__main__":
    config_manager = ConfigManager('config.ini')
    module = Buttons(config_manager)
    logger = module.logger(module.logfile, module.max_log_size, module.max_archive_size)

    # Get initial values
    min_humidity = config_manager.get_int_config('min_humidity')
    max_humidity = config_manager.get_int_config('max_humidity')
    # Get button pins
    up_button_pin = config_manager.get_int_config('up_button_pin')
    dn_button_pin = config_manager.get_int_config('dn_button_pin')

    # GPIO setup using gpiozero
    up_button = Button(up_button_pin, pull_up=True, bounce_time=0.2, hold_time=2)
    dn_button = Button(dn_button_pin, pull_up=True, bounce_time=0.2, hold_time=2)

    # Variables to manage button state and humidity values
    last_press_time = {'up': 0, 'dn': 0}
    button_hold_time = 2
    button_pressed = {'up': False, 'dn': False}
    humidity_changed = False
    mode = None

    # Attach event handlers
    up_button.when_pressed = button_pressed_callback
    up_button.when_held = button_hold_callback

    dn_button.when_pressed = button_pressed_callback
    dn_button.when_held = button_hold_callback

    # Start the button hold check thread
    # threading.Thread(target=button_hold_check, daemon=True).start()

    # Initialize lines
    lines = [""] * 4  # For four line ssd1306_display...

    try:
        time.sleep(3)
        start_time = time.time()
        while True:
            current_time = time.time()
            # Read and print sensor data every 2 seconds
            if int(current_time - start_time) % 1 == 0:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                time.sleep(.1)  # Adjust as needed

            # Heat the sensors every 90 seconds
            if int(current_time - start_time) % 90 == 0:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print("Heating External sensor...")
                logger.log(timestamp, 'External', '01', "Heating External sensor...")

                print("Heating Internal sensor...")
                logger.log(timestamp, 'Internal', '02', "Heating Internal sensor...")

            # Sleep for a short duration to avoid multiple reads/heats within the same second
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected!")

    finally:
        cleanup()
