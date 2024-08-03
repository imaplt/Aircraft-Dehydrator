
import sys
import schedule
import time
from config_manager import ConfigManager
from logger import Logger as Log
import system_status
from display import SSD1306Display, LCD2004Display, DisplayConfig
from gpiozero import Button
from sensor import Sensor


def task_internal():
    print("Task running every second")


def task_external():
    print("Task running every minute")


def schedule_tasks(int_interval=1, ext_interval=15):
    schedule.every(int_interval).seconds.do(task_internal)
    schedule.every(ext_interval).minutes.do(task_external)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def read_installed_devices(config):
    devices = config.get_config('installed_devices').split(',')
    devices = [device.strip() for device in devices]  # Remove any extra whitespace
    return devices


def display_min_humidity(value):
    print(f"Min Humidity: {value}%")


def display_max_humidity(value):
    print(f"Max Humidity: {value}%")


def save_config():
    global MIN_HUMIDITY, MAX_HUMIDITY
    print("Saving config...")
    print("Min Humidity: ", MIN_HUMIDITY)
    print("Max Humidity: ", MAX_HUMIDITY)
    configManager.update_config('min_humidity', MIN_HUMIDITY)
    configManager.update_config('max_humidity', MAX_HUMIDITY)


def button_pressed_callback(button):
    global MIN_HUMIDITY, MAX_HUMIDITY, last_press_time, humidity_changed, mode

    now = time.time()
    button_name = 'up' if button.pin.number == UP_BUTTON_PIN else 'dn'
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
            display_max_humidity(MAX_HUMIDITY)
        else:
            print('DN Button Pressed...')
            display_min_humidity(MIN_HUMIDITY)
    else:
        now = time.time()
        if mode == 'max':
            if button_name == 'up':
                MAX_HUMIDITY += 1
                display_max_humidity(MAX_HUMIDITY)
                humidity_changed = True
                last_press_time['up'] = now
            elif button_name == 'dn':
                MAX_HUMIDITY -= 1
                display_max_humidity(MAX_HUMIDITY)
                humidity_changed = True
                last_press_time['dn'] = now
        elif mode == 'min':
            if button_name == 'up':
                MIN_HUMIDITY += 1
                display_min_humidity(MIN_HUMIDITY)
                humidity_changed = True
                last_press_time['up'] = now
            elif button_name == 'dn':
                MIN_HUMIDITY -= 1
                display_min_humidity(MIN_HUMIDITY)
                humidity_changed = True
                last_press_time['dn'] = now


def button_hold_callback(button):
    global MIN_HUMIDITY, MAX_HUMIDITY, last_press_time, humidity_changed, mode

    button_name = 'up' if button.pin.number == UP_BUTTON_PIN else 'dn'
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
        display_max_humidity(MAX_HUMIDITY)
        mode = 'max'
    else:
        print('DN Button Held...')
        display_min_humidity(MIN_HUMIDITY)
        mode = 'min'


def cleanup():
    # Want to add code here to update display, update log with run time etc
    print('Cleaning Up')
    # ssd1306_display.display_text_center_with_border('Shutting down...')
    # lcd2004_display.display_text_with_border('Shutting down...')
    logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
               'System', '', "Shutting down...")
    time.sleep(3)
    # ssd1306_display.clear_screen()
    # lcd2004_display.clear()


if __name__ == "__main__":
    # Get configuration items
    configManager = ConfigManager('config.ini')
    LOGFILE = configManager.get_config('logfile')
    MAX_LOG_SIZE = configManager.get_int_config('max_log_size')
    MAX_ARCHIVE_SIZE = configManager.get_int_config('max_archive_size')
    MIN_HUMIDITY = configManager.get_int_config('min_humidity')
    MAX_HUMIDITY = configManager.get_int_config('max_humidity')

    # Get button pin info
    UP_BUTTON_PIN = configManager.get_int_config('up_button_pin')
    DN_BUTTON_PIN = configManager.get_int_config('dn_button_pin')

    # Get display related config info
    FONT = configManager.get_config('font')
    FONTSIZE = configManager.get_int_config('fontsize')
    BORDER = configManager.get_int_config('border')

    # Initialise the logging
    logger = Log(LOGFILE, MAX_LOG_SIZE, MAX_ARCHIVE_SIZE)

    # GPIO setup using gpiozero
    up_button = Button(UP_BUTTON_PIN, pull_up=True, bounce_time=0.2, hold_time=3)
    dn_button = Button(DN_BUTTON_PIN, pull_up=True, bounce_time=0.2, hold_time=3)

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
        installed_devices = read_installed_devices(configManager)
        overall_status, statuses = system_status.query_i2c_devices(installed_devices)
        print(f"Overall status: {overall_status}")

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for status in statuses:
            print(status)
            logger.log(timestamp, 'System', '', status)
        if overall_status == 'bad':
            logger.log(timestamp, 'System', 'Overall', "Overall Status: Fail")
            print("Overall Status: Fail")
            raise ValueError("Overall Status Failed")

        schedule_tasks()
        # run_scheduler()

        ssd1306_display_config = DisplayConfig(font_path=FONT, font_size=FONTSIZE, border_size=BORDER)
        ssd1306Display = SSD1306Display(ssd1306_display_config)
        lcd2004Display = LCD2004Display()

        # Display centered text
        ssd1306Display.display_text_center("Initializing...")
        lcd2004Display.display_text_with_border(['Initializing...'])
        time.sleep(3)
        internalsensor = Sensor('SHT41_Internal', 0x44)
        externalsensor = Sensor('SHT30', 0x44)

        # Initialize previous output values to None
        internalprevious_output = {'temperature': 0, 'humidity': 0}
        externalprevious_output = {'temperature': 0, 'humidity': 0}

        print("External Mode: ", externalsensor.sensor_mode())
        print("Internal Mode: ", internalsensor.sensor_mode())

        ssd1306Display.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."],
                                                 justification='left')
        ssd1306Display.display_default_four_rows()
        time.sleep(2)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected!")

    finally:
        cleanup()
#
# self.logfile = self.config_manager.get_config('logfile')
# self.min_humidity = self.config_manager.get_int_config('min_humidity')
# self.max_humidity = self.config_manager.get_int_config('max_humidity')
# self.font = self.config_manager.get_config('font')
# self.fontsize = self.config_manager.get_int_config('fontsize')
# self.border = self.config_manager.get_int_config('border')
# self.max_log_size = self.config_manager.get_int_config('max_log_size')
# self.max_archive_size = self.config_manager.get_int_config('max_archive_size')
