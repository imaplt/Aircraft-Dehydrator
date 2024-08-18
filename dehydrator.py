
import schedule
import time
import functools
from datetime import timedelta
from config_manager import ConfigManager
from logger import Logger as Log
import system_status
from display import SSD1306Display, LCD2004Display, DisplayConfig
from gpiozero import Button
from sensor import Sensor
from fan_controller import EMC2101


# This decorator can be applied to any job function to log the elapsed time of each job
# Use this to account for jobs taking longer than expected...
def print_elapsed_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_timestamp = time.time()
        result = func(*args, **kwargs)
        if time.time() - start_timestamp > 0:
            print('LOG: Running job "%s"' % func.__name__)
            print('LOG: Job "%s" completed in %d seconds' % (func.__name__, time.time() - start_timestamp))
        return result
    return wrapper


# @print_elapsed_time
def task_internal():
    global INTERNAL_HIGH_TEMP, INTERNAL_HIGH_HUMIDITY, INTERNAL_LOW_TEMP, INTERNAL_LOW_HUMIDITY, \
        CYCLE_COUNT, TOTAL_CYCLE_DURATION, FAN_RUNNING, RUNNING_TIME, MAX_FAN_RUNTIME
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    internaloutput = internalsensor.read_sensor()

    # Update the config file with stats
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
        logger.log(timestamp, 'INFO', 'SENSORS', 'INTERNAL',
                   f"Temperature: {internaloutput['temperature']}C,"
                   f" Humidity: {internaloutput['humidity']}%")
        # Update previous output values
        internalprevious_output['temperature'] = internaloutput['temperature']
        internalprevious_output['humidity'] = internaloutput['humidity']
        print("Internal Sensor Reading:", internaloutput)
        ssd1306Display.update_line(1, justification='left',
                                   text=f"{internaloutput['humidity']}%" f" - {internaloutput['temperature']}°C")
        if internaloutput['humidity'] > MAX_HUMIDITY:
            started, run_time = fanController.set_fan_speed(100)
            if started:
                logger.log(timestamp, 'INFO', 'SYSTEM', 'FAN',
                           f"Fan started, exceeded MAX humidity of {MAX_HUMIDITY}%")
                print(f"Fan started, exceeded set humidity of: {MAX_HUMIDITY}%")
                ssd1306Display.display_text_center_with_border('Fan Started...')
                FAN_RUNNING = True
                time.sleep(1)
                # Reset display back to previous lines
                ssd1306Display.display_four_rows_center(ssd1306Display.oled_lines, justification='left')
            if timedelta(seconds=run_time) > MAX_FAN_RUNTIME:
                MAX_FAN_RUNTIME = timedelta(seconds=run_time)
            if timedelta(seconds=run_time) > FAN_LIMIT:
                # TODO: Add FAN_LIMIT logic, maybe a method or function?
                print("Fan limit exceeded")
                logger.log(timestamp, 'WARN', 'SYSTEM', 'FAN',
                           f"Fan time limit exceeded: {FAN_LIMIT}")
                _fan_limit_exceeded()
        elif internaloutput['humidity'] < MIN_HUMIDITY:
            stopped, run_time = fanController.set_fan_speed(0)
            if stopped:
                print(f"Fan stopped, passed MIN humidity of: {MIN_HUMIDITY }%")
                logger.log(timestamp, 'INFO', 'SYSTEM', 'FAN',
                           f"Fan stopped, passed MIN humidity of: {MIN_HUMIDITY }%")
                logger.log(timestamp, 'INFO', 'SYSTEM', 'FAN', f"Fan run time: {str(timedelta(seconds=run_time))}")
                TOTAL_CYCLE_DURATION += timedelta(seconds=run_time)
                CYCLE_COUNT += 1
                FAN_RUNNING = False
                if RUNNING_TIME > MAX_FAN_RUNTIME:
                    MAX_FAN_RUNTIME = RUNNING_TIME
                if RUNNING_TIME > FAN_LIMIT:
                    # TODO: Add FAN_LIMIT logic, maybe a method or function?
                    print("Fan limit exceeded")
                    logger.log(timestamp, 'WARN', 'SYSTEM', 'FAN',
                               f"Fan time limit exceeded: {FAN_LIMIT}%")
                    _fan_limit_exceeded()
                RUNNING_TIME = 0
                save_config()
                ssd1306Display.display_text_center_with_border('Fan Stopped...')
                time.sleep(1)
                # Reset display back to prev lines
                ssd1306Display.display_four_rows_center(ssd1306Display.oled_lines, justification='left')
    time.sleep(.1)  # Adjust as needed


# @print_elapsed_time
def task_external():
    global EXTERNAL_LOW_TEMP, EXTERNAL_HIGH_TEMP, EXTERNAL_HIGH_HUMIDITY, EXTERNAL_LOW_HUMIDITY

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    externaloutput = externalsensor.read_sensor()
    # Update the config file with stats
    log_changed = False

    if externaloutput['humidity'] > EXTERNAL_HIGH_HUMIDITY:
        EXTERNAL_HIGH_HUMIDITY = externaloutput['humidity']
        log_changed = True
    elif externaloutput['humidity'] < EXTERNAL_LOW_HUMIDITY:
        EXTERNAL_LOW_HUMIDITY = externaloutput['humidity']
        log_changed = True

    # Update high and low temperature for external values
    if externaloutput['temperature'] > EXTERNAL_HIGH_TEMP:
        EXTERNAL_HIGH_TEMP = externaloutput['temperature']
        log_changed = True
    elif externaloutput['temperature'] < EXTERNAL_LOW_TEMP:
        EXTERNAL_LOW_TEMP = externaloutput['temperature']
        log_changed = True

    if log_changed:
        save_config()

    # No need to check differences as this will be logged every x seconds unlike the internal one
    logger.log(timestamp, 'INFO', 'SENSORS', 'EXTERNAL',
               f"Temperature: {externaloutput['temperature']}C,"
               f" Humidity: {externaloutput['humidity']}%")
    # Update previous output values
    externalprevious_output['temperature'] = externaloutput['temperature']
    externalprevious_output['humidity'] = externaloutput['humidity']
    print("External Sensor Reading:", externaloutput)
    ssd1306Display.update_line(3, justification='left',
                               text=f"{externaloutput['humidity']}% - {externaloutput['temperature']}°C")
    time.sleep(.1)


#  @print_elapsed_time
def _cycle_fan():
    # TODO: How do we want to engage this?
    logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
               'INFO', 'SYSTEM', 'FAN', "Fan Cycle Started...")
    print("Fan Cycle Started...")
    fanController.set_fan_speed(50)
    time.sleep(FAN_DURATION)
    fanController.set_fan_speed(0)


def lcd_display(screen_no):
    global lcd_lines
    if screen_no == 1:
        lcd_lines[0] = f"Int Max:{INTERNAL_HIGH_TEMP}C {INTERNAL_HIGH_HUMIDITY}%"
        lcd_lines[1] = f"Int Min:{INTERNAL_LOW_TEMP}C {INTERNAL_LOW_HUMIDITY}%"
        lcd_lines[2] = f"Ext Max:{EXTERNAL_HIGH_TEMP}C {EXTERNAL_HIGH_HUMIDITY}%"
        lcd_lines[3] = f"Ext Min:{EXTERNAL_LOW_TEMP}C {EXTERNAL_LOW_HUMIDITY}%"
        lcd2004Display.display_four_rows_center(lcd_lines, justification='left')
    else:
        lcd_lines[0] = "Fan Stats..."
        lcd_lines[1] = f"Cycles: {CYCLE_COUNT}"
        lcd_lines[2] = f"Duration: {TOTAL_CYCLE_DURATION}"
        lcd_lines[3] = f"Running - {str(FAN_RUNNING)}"
        lcd2004Display.display_four_rows_center(lcd_lines, justification='left')


def oled_display():
    global lcd_lines
    lcd_lines[0] = f"Int Max:{INTERNAL_HIGH_TEMP}C {INTERNAL_HIGH_HUMIDITY}%"
    lcd_lines[1] = f"Int Min:{INTERNAL_LOW_TEMP}C {INTERNAL_LOW_HUMIDITY}%"
    lcd_lines[2] = f"Ext Max:{EXTERNAL_HIGH_TEMP}C {EXTERNAL_HIGH_HUMIDITY}%"
    lcd_lines[3] = f"Ext Min:{EXTERNAL_LOW_TEMP}C {EXTERNAL_LOW_HUMIDITY}%"
    lcd2004Display.display_four_rows_center(lcd_lines, justification='left')


# Task to alternate screens
def task_alternate_screens():
    if task_alternate_screens.current_screen == 1:
        lcd_display(1)
        task_alternate_screens.current_screen = 2
    else:
        lcd_display(2)
        task_alternate_screens.current_screen = 1


def schedule_tasks(int_interval=1, ext_interval=5, fan_interval=1, display_interval=30):
    schedule.every(int_interval).seconds.do(task_internal)
    schedule.every(ext_interval).minutes.do(task_external)
    # schedule.every(fan_interval).minutes.do(task_fan)
    if DISPLAY_ENABLED:
        schedule.every(display_interval).seconds.do(task_alternate_screens)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def heat_sensor():
    # TODO: Add code to heat sensors when the humidity gets high. Only applies to SHT4X series sensors
    print("Heating External sensor...")
    externalsensor.heat_sensor()
    logger.log(timestamp, 'INFO', 'SYSTEM', 'EXTERNAL', "Heating External sensor...")

    print("Heating Internal sensor...")
    internalsensor.heat_sensor()
    logger.log(timestamp, 'INFO', 'SYSTEM', 'INTERNAL', "Heating Internal sensor...")


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
    global CYCLE_COUNT, TOTAL_CYCLE_DURATION, MAX_FAN_RUNTIME

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
    configManager.set_duration_config('total_cycle_duration', TOTAL_CYCLE_DURATION, 'LOG')
    configManager.set_duration_config('MAX_FAN_RUNTIME', MAX_FAN_RUNTIME, 'LOG')


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
    elif mode == 'config':
        if button_name == 'up':
            print('Up Config Button Pressed...', mode)
        else:
            print('DN Config Button Pressed...')
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

    if up_button.is_active and dn_button.is_active:
        if mode != 'config':
            print("Both buttons are being held...")
            schedule.clear()
            time.sleep(.2)
            print('Starting schedular again...')
            lcd2004Display.display_text_with_border(['Configuration Mode'])
            time.sleep(10)
            mode = 'config'
            return

    if button_name == 'up':
        print('Up Button Held...')
        display_max_humidity(MAX_HUMIDITY)
        mode = 'max'
    else:
        print('DN Button Held...')
        display_min_humidity(MIN_HUMIDITY)
        mode = 'min'
    time.sleep(.2)


def _fan_limit_exceeded():
    # TODO: Should this be a hard limit? Some way to change this maybe?
    # Cancel all teh jobs
    schedule.clear()
    ssd1306Display.display_text_center_with_border('FAN LIMIT EXCEEDED')
    lcd2004Display.display_text_with_border(['FAN LIMIT EXCEEDED'])
    fanController.set_fan_speed(0)
    save_config()
    while True:
        time.sleep(1)


def cleanup():
    # Want to add code here to update display, update log with run time etc
    print('Cleaning Up')
    try:
        ssd1306Display.display_text_center_with_border('Shutting down...')
        lcd2004Display.display_text_with_border(['Shutting down...'])
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO',
                   'System', 'System', "Shutting down...")
        # make sure fan is off
        fanController.set_fan_speed(0)
        time.sleep(3)
        ssd1306Display.clear_screen()
        lcd2004Display.clear()
    except NameError:
        print('LCD Not Defined')
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'FATAL',
                   'System', 'System', "No display available...")
    finally:
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'FATAL',
                   'System', 'System', "System Shutting down..")


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
    TASK_FAN = configManager.get_int_config('TASK_FAN')
    TASK_INTERNAL = configManager.get_int_config('TASK_INTERNAL')
    TASK_EXTERNAL = configManager.get_int_config('TASK_EXTERNAL')
    TASK_DISPLAY_ROTATION = configManager.get_int_config('TASK_DISPLAY_ROTATION')
    LCD_ROTATION = configManager.get_int_config('LCD_ROTATION')
    OLED_ROTATION = configManager.get_int_config('OLED_ROTATION')

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
    MAX_FAN_RUNTIME = configManager.get_duration_config('LOG', 'MAX_FAN_RUNTIME')
    FAN_LIMIT = configManager.get_duration_config('DEFAULT', 'FAN_LIMIT')

    # Display configuration
    DISPLAY_ENABLED = configManager.get_boolean_config('DISPLAY_ENABLED')

    # Initialize current screen
    task_alternate_screens.current_screen = 1

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

    # Initialize lines
    oled_lines = [""] * 4  # For four line ssd1306_display...
    lcd_lines = [""] * 4  # For four line ssd1306_display...

    FAN_RUNNING = False
    RUNNING_TIME = 0
    try:
        installed_devices = read_installed_devices(configManager)
        overall_status, statuses = system_status.query_i2c_devices(installed_devices)
        print(f"Overall status: {overall_status}")

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for status in statuses:
            print(status)
            logger.log(timestamp, 'INFO', 'SYSTEM', 'STATUS', status)

        if overall_status == 'bad':
            logger.log(timestamp, 'WARN', 'SYSTEM', 'OVERALL', "Overall Status: Fail")
            print("Overall Status: Fail")
            raise ValueError("Overall Status Failed")

        # Initialize fan controller
        fanController = EMC2101()

        # Initialize displays...
        # Need to do this first so if there is an error cleanup can still work...
        ssd1306_display_config = DisplayConfig(font_path=FONT, font_size=FONTSIZE, border_size=BORDER)
        ssd1306Display = SSD1306Display(ssd1306_display_config)
        if isDeviceDetected(statuses, 'LCD2004'):
            lcd2004Display = LCD2004Display()
            lcd2004Display.clear()
            lcd2004Display.display_text_with_border(['Initializing...'])

        # Display centered text
        ssd1306Display.display_text_center("Initializing...")

        time.sleep(3)
        internalsensor = Sensor('SHT41_Internal', 0x44)

        # sht30_sensor = Sensor('SHT30', 0x44)
        # print(sht30_sensor.sensor.relative_humidity, sht30_sensor.sensor.temperature)

        if isDeviceDetected(statuses, 'SHTC3'):
            externalsensor = Sensor('SHTC3', 0x70)
            externalprevious_output = {'temperature': 0, 'humidity': 0}

        # Initialize previous output values to None
        internalprevious_output = {'temperature': 0, 'humidity': 0}

        print("Internal Mode: ", internalsensor.sensor_mode())  # TODO: Figure out what mode is...
        ssd1306Display.display_default_four_rows()
        time.sleep(2)
        schedule_tasks(int_interval=TASK_INTERNAL, ext_interval=TASK_EXTERNAL,
                       fan_interval=TASK_FAN, display_interval=TASK_DISPLAY_ROTATION)

        # Need to run the External once to update the values
        task_external()
        if DISPLAY_ENABLED:
            lcd_display(1)

        run_scheduler()

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected!")

    except ValueError as e:
        #  TODO: Systems has failed, what to do next?
        print("\nValue Error!",e)

    except OSError:
        print("\nOS Error!")

    except NameError:
        print("\nName Error!")

    finally:
        cleanup()
