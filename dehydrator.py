
import schedule
import time
from datetime import timedelta
from config_manager import ConfigManager
from logger import Logger as Log
import system_status
from display import SSD1306Display, LCD2004Display, DisplayConfig
from gpiozero import Button
from sensor import Sensor
from fan_controller import EMC2101


def task_internal():
    global INTERNAL_HIGH_TEMP, INTERNAL_HIGH_HUMIDITY, INTERNAL_LOW_TEMP, INTERNAL_LOW_HUMIDITY, \
        CYCLE_COUNT, TOTAL_CYCLE_DURATION
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    internaloutput = internalsensor.read_sensor()

    # Update the config file with stats..
    log_changed = False
    # Update high and low humidity
    if internaloutput['humidity'] > INTERNAL_HIGH_HUMIDITY:
        INTERNAL_HIGH_HUMIDITY = internaloutput['humidity']
        log_changed = True
    elif internaloutput['humidity'] < INTERNAL_LOW_HUMIDITY:
        INTERNAL_LOW_HUMIDITY = internaloutput['humidity']
        log_changed = True

    # Update high and low temperature
    if internaloutput['temperature'] > INTERNAL_HIGH_TEMP:
        INTERNAL_HIGH_TEMP = internaloutput['temperature']
        log_changed = True
    elif internaloutput['temperature'] < INTERNAL_LOW_TEMP:
        INTERNAL_LOW_TEMP = internaloutput['temperature']
        log_changed = True

    if log_changed:
        save_config()

    if abs(internaloutput['humidity'] - internalprevious_output['humidity']) > 0.2:
        logger.log(timestamp, 'Sensors', 'Internal',
                   f"Temperature: {internaloutput['temperature']}C,"
                   f" Humidity: {internaloutput['humidity']}%")
        # Update previous output values
        internalprevious_output['temperature'] = internaloutput['temperature']
        internalprevious_output['humidity'] = internaloutput['humidity']
        print("Internal Sensor Reading:", internaloutput)
        ssd1306Display.update_line(1, justification='left',
                                   text=f"{internaloutput['humidity']}%" f" - {internaloutput['temperature']}°C")
        if internaloutput['humidity'] > MAX_HUMIDITY:
            started = fanController.set_fan_speed(100)
            if started:
                logger.log(timestamp, 'Fan', '',
                           f"Fan started, exceeded MAX humidity of: {MAX_HUMIDITY}%")
                print(f"Fan started, exceeded set humidity of: {MAX_HUMIDITY}%")
                ssd1306Display.display_text_center_with_border('Fan Started...')
                time.sleep(1)
                ssd1306Display.display_default_four_rows()
        elif internaloutput['humidity'] < MIN_HUMIDITY:
            stopped, run_time = fanController.set_fan_speed(0)
            if stopped:
                print(f"Fan stopped, passed MIN humidity of: {MIN_HUMIDITY }%")
                logger.log(timestamp, 'Fan', '',
                           f"Fan stopped, passed MIN humidity of: {MIN_HUMIDITY }%")
                logger.log(timestamp, 'Fan', '', f"Fan run time: {str(timedelta(seconds=run_time))}")
                TOTAL_CYCLE_DURATION += timedelta(seconds=run_time)
                CYCLE_COUNT += 1
                save_config()
                ssd1306Display.display_text_center_with_border('Fan Stopped...')
                time.sleep(1)
                ssd1306Display.display_default_four_rows()
    time.sleep(.1)  # Adjust as needed


def task_external():
    global EXTERNAL_LOW_TEMP, EXTERNAL_HIGH_TEMP, EXTERNAL_HIGH_HUMIDITY, EXTERNAL_LOW_HUMIDITY

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    externaloutput = externalsensor.read_sensor()
    # Update the config file with stats..
    log_changed = False

    if externaloutput['humidity'] > EXTERNAL_HIGH_HUMIDITY:
        EXTERNAL_HIGH_HUMIDITY = externaloutput['humidity']
        external_humidity_changed = True
    elif externaloutput['humidity'] < EXTERNAL_LOW_HUMIDITY:
        EXTERNAL_LOW_HUMIDITY = externaloutput['humidity']
        external_humidity_changed = True

    # Update high and low temperature for external values
    if externaloutput['temperature'] > EXTERNAL_HIGH_TEMP:
        EXTERNAL_HIGH_TEMP = externaloutput['temperature']
        external_temperature_changed = True
    elif externaloutput['temperature'] < EXTERNAL_LOW_TEMP:
        EXTERNAL_LOW_TEMP = externaloutput['temperature']
        external_temperature_changed = True

    if log_changed:
        save_config()

    if abs(externaloutput['humidity'] - externalprevious_output['humidity']) > 0.2:
        logger.log(timestamp, 'Sensors', 'External',
                   f"Temperature: {externaloutput['temperature']}C,"
                   f" Humidity: {externaloutput['humidity']}%")
        # Update previous output values
        externalprevious_output['temperature'] = externaloutput['temperature']
        externalprevious_output['humidity'] = externaloutput['humidity']
        print("External Sensor Reading:", externaloutput)
        ssd1306Display.update_line(3, justification='left',
                                   text=f"{externaloutput['humidity']}% - {externaloutput['temperature']}°C")
    time.sleep(.1)


def task_fan():
    # TODO: A better way to cycle the fan
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.log(timestamp, 'System', 'Fan', "Fan Cycle Started...")
    print("Fan Cycle Started...")
    fanController.set_fan_speed(50)
    time.sleep(FAN_DURATION)
    fanController.set_fan_speed(0)


def task_display():
    lines[0] = f"Max T:{INTERNAL_HIGH_TEMP} H:{INTERNAL_HIGH_HUMIDITY}"
    lines[1] = f"Min T:{INTERNAL_LOW_TEMP} Min H:{INTERNAL_LOW_HUMIDITY}"
    lines[2] = f"Max T:{EXTERNAL_HIGH_TEMP} Max H:{EXTERNAL_HIGH_HUMIDITY}"
    lines[3] = f"Min T:{EXTERNAL_LOW_TEMP} Min H:{EXTERNAL_LOW_HUMIDITY}"
    lcd2004Display.display_four_rows_center(lines)


def schedule_tasks(int_interval=1, ext_interval=1, fan_interval=1, display_interval=30):
    schedule.every(int_interval).seconds.do(task_internal)
    schedule.every(ext_interval).minutes.do(task_external)
    schedule.every(fan_interval).minutes.do(task_fan)
    if DISPLAY_ENABLED:
        schedule.every(display_interval).seconds.do(task_display)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def heat_sensor():
    # TODO: Add code to heat sensors when the humidity gets high.
    print("Heating External sensor...")
    externalsensor.heat_sensor()
    logger.log(timestamp, 'External', '01', "Heating External sensor...")

    print("Heating Internal sensor...")
    internalsensor.heat_sensor()
    logger.log(timestamp, 'Internal', '02', "Heating Internal sensor...")


def read_installed_devices(config):
    devices = config.get_config('installed_devices').split(',')
    devices = [device.strip() for device in devices]  # Remove any extra whitespace
    return devices


def display_min_humidity(value):
    print(f"Min Humidity: {value}%")


def display_max_humidity(value):
    print(f"Max Humidity: {value}%")


def save_config():
    global MIN_HUMIDITY, MAX_HUMIDITY, INTERNAL_LOW_HUMIDITY, INTERNAL_HIGH_HUMIDITY
    global INTERNAL_HIGH_TEMP, INTERNAL_HIGH_HUMIDITY, EXTERNAL_LOW_TEMP, EXTERNAL_HIGH_TEMP
    global EXTERNAL_LOW_HUMIDITY, EXTERNAL_HIGH_HUMIDITY, EXTERNAL_LOW_TEMP, EXTERNAL_HIGH_TEMP
    global CYCLE_COUNT, TOTAL_CYCLE_DURATION
    print("Saving config...")
    print("Min Humidity: ", MIN_HUMIDITY)
    print("Max Humidity: ", MAX_HUMIDITY)
    print('CYCLE_COUNT: ', CYCLE_COUNT)
    print('TOTAL_CYCLE_DURATION: ', TOTAL_CYCLE_DURATION)
    print('Internal High Temperature: ', INTERNAL_HIGH_TEMP)
    print('External High Temperature: ', EXTERNAL_HIGH_TEMP)
    print('Internal Low Temperature: ', INTERNAL_LOW_TEMP)
    print('External Low Temperature: ', EXTERNAL_LOW_TEMP)
    print('Internal Low Humidity: ', INTERNAL_LOW_HUMIDITY)
    print('Internal High Humidity: ', INTERNAL_HIGH_HUMIDITY)
    print('External Low Humidity: ', EXTERNAL_LOW_HUMIDITY)
    print('External High Humidity: ', EXTERNAL_HIGH_HUMIDITY)

    configManager.update_config('min_humidity', MIN_HUMIDITY)
    configManager.update_config('max_humidity', MAX_HUMIDITY)
    configManager.update_config('internal_high_temp', INTERNAL_HIGH_TEMP, 'LOG')
    configManager.update_config('internal_low_temp', INTERNAL_LOW_TEMP, 'LOG')
    configManager.update_config('internal_high_humidity', INTERNAL_HIGH_HUMIDITY, 'LOG')
    configManager.update_config('internal_low_humidity', INTERNAL_LOW_HUMIDITY, 'LOG')
    configManager.update_config('external_high_temp', EXTERNAL_HIGH_TEMP, 'LOG')
    configManager.update_config('external_low_temp', EXTERNAL_LOW_TEMP, 'LOG')
    configManager.update_config('external_high_humidity', EXTERNAL_HIGH_HUMIDITY, 'LOG')
    configManager.update_config('external_low_humidity', EXTERNAL_LOW_HUMIDITY, 'LOG')
    configManager.update_config('cycle_count', CYCLE_COUNT, 'LOG')
    configManager.update_config('total_cycle_duration', TOTAL_CYCLE_DURATION, 'LOG')


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
    ssd1306Display.display_text_center_with_border('Shutting down...')
    lcd2004Display.display_text_with_border(['Shutting down...'])
    logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
               'System', 'System', "Shutting down...")
    time.sleep(3)
    ssd1306Display.clear_screen()
    lcd2004Display.clear()


def isDeviceDetected(statuses, device):
    for status in statuses:
        if device in status and 'Detected' in status:
            return True
    return False


if __name__ == "__main__":
    # Get configuration items
    configManager = ConfigManager('config.ini')
    LOGFILE = configManager.get_config('logfile')
    MAX_LOG_SIZE = configManager.get_int_config('max_log_size')
    MAX_ARCHIVE_SIZE = configManager.get_int_config('max_archive_size')
    MIN_HUMIDITY = configManager.get_int_config('min_humidity')
    MAX_HUMIDITY = configManager.get_int_config('max_humidity')
    FAN_DURATION = configManager.get_int_config('fan_duration')
    # Set task intervals
    TASK_FAN = configManager.get_int_config('task_fan')
    TASK_INTERNAL = configManager.get_int_config('task_internal')
    TASK_EXTERNAL = configManager.get_int_config('task_external')
    TASK_DISPLAY = configManager.get_int_config('task_display')

    # Get button pin info
    UP_BUTTON_PIN = configManager.get_int_config('up_button_pin')
    DN_BUTTON_PIN = configManager.get_int_config('dn_button_pin')

    # Get display related config info
    FONT = configManager.get_config('font')
    FONTSIZE = configManager.get_int_config('fontsize')
    BORDER = configManager.get_int_config('border')

    # Initialise the logging and pull numbers from the config.
    logger = Log(LOGFILE, MAX_LOG_SIZE, MAX_ARCHIVE_SIZE)
    INTERNAL_HIGH_TEMP = configManager.get_float_config('LOG', 'internal_high_temp')
    INTERNAL_LOW_TEMP = configManager.get_float_config('LOG', 'internal_low_temp')
    INTERNAL_HIGH_HUMIDITY = configManager.get_float_config('LOG', 'internal_high_humidity')
    INTERNAL_LOW_HUMIDITY = configManager.get_float_config('LOG', 'internal_low_humidity')
    EXTERNAL_HIGH_TEMP = configManager.get_float_config('LOG', 'external_high_temp')
    EXTERNAL_LOW_TEMP = configManager.get_float_config('LOG', 'external_low_temp')
    EXTERNAL_HIGH_HUMIDITY = configManager.get_float_config('LOG', 'external_high_humidity')
    EXTERNAL_LOW_HUMIDITY = configManager.get_float_config('LOG', 'external_low_humidity')
    CYCLE_COUNT = configManager.get_int_config('cycle_count')
    TOTAL_CYCLE_DURATION = configManager.get_duration_config('LOG', 'total_cycle_duration')

    # Display configuration
    DISPLAY_ENABLED = configManager.get_boolean_config('DISPLAY_ENABLED')

    # GPIO setup using gpiozero for input buttons
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

    # Initialize fan controller
    fanController = EMC2101()

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

            # Initialize displays...
        ssd1306_display_config = DisplayConfig(font_path=FONT, font_size=FONTSIZE, border_size=BORDER)
        ssd1306Display = SSD1306Display(ssd1306_display_config)
        lcd2004Display = LCD2004Display()
        lcd2004Display.clear()

        # Display centered text
        ssd1306Display.display_text_center("Initializing...")
        lcd2004Display.display_text_with_border(['Initializing...'])
        time.sleep(3)
        internalsensor = Sensor('SHT41_Internal', 0x44)

        if isDeviceDetected(statuses, 'SHTC3'):
            externalsensor = Sensor('SHTC3', 0x70)
            externalprevious_output = {'temperature': 0, 'humidity': 0}

        # Initialize previous output values to None
        internalprevious_output = {'temperature': 0, 'humidity': 0}

        print("Internal Mode: ", internalsensor.sensor_mode())

        ssd1306Display.display_four_rows_center(["Internal:", "reading...", "External:", "reading..."],
                                                justification='left')
        ssd1306Display.display_default_four_rows()
        time.sleep(2)
        schedule_tasks(int_interval=TASK_INTERNAL, ext_interval=TASK_EXTERNAL, fan_interval=TASK_FAN)

        # Need to run the External once to update the values
        task_external()
        if DISPLAY_ENABLED:
            task_display()
        run_scheduler()

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected!")

    finally:
        cleanup()
