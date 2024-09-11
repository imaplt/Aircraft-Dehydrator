
import schedule
import time
import functools
from datetime import timedelta
from config_manager import ConfigManager
from logger import Logger as Log
import system_status
from display import BONNETDisplay, LCD2004Display, DisplayConfig
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

def celsius_to_fahrenheit(celsius):
    fahrenheit = (celsius * 9/5) + 32
    return round(fahrenheit, 1)

# @print_elapsed_time
def task_internal():
    global INTERNAL_HIGH_TEMP, INTERNAL_HIGH_HUMIDITY, INTERNAL_LOW_TEMP, INTERNAL_LOW_HUMIDITY, \
        CYCLE_COUNT, FAN_TOTAL_DURATION, FAN_RUNNING, FAN_RUNNING_TIME, FAN_MAX_RUNTIME,\
        INTERNAL_TEMP, INTERNAL_HUMIDITY, current_page

    if fanController.fan_engaged and current_page == 1:
        FAN_RUNNING_TIME = timedelta(seconds=(int(time.time() -  fanController.start_time)))
        display_fan_stats()

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
        INTERNAL_HUMIDITY = internaloutput['humidity']
        INTERNAL_TEMP = internaloutput['temperature']
        if current_page == 0:
            BONNETDisplay.update_line(1, text=f"{INTERNAL_HUMIDITY}%" f" - {INTERNAL_TEMP}°C", justification='left')
        if internaloutput['humidity'] > MAX_HUMIDITY:
            started, run_time = fanController.set_fan_speed(100)
            if started:
                # Set start time here.
                fanController.start_time = time.time()
                logger.log(timestamp, 'INFO', 'SYSTEM', 'FAN',
                           f"Fan started, exceeded MAX humidity of {MAX_HUMIDITY}%")
                print(f"Fan started, exceeded set humidity of: {MAX_HUMIDITY}%")
                # TODO: Update to save current page and then return
                BONNETDisplay.display_text_center_with_border('Fan Started...')
                FAN_RUNNING = True
                time.sleep(1)
                # Reset display back to previous lines
                display_fan_stats()
                # BONNETDisplay.display_rows_center(BONNETDisplay.oled_lines, justification='left')
                print(run_time, FAN_MAX_RUNTIME, FAN_LIMIT)
            if timedelta(seconds=run_time) > FAN_MAX_RUNTIME:
                FAN_MAX_RUNTIME = timedelta(seconds=run_time)
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
                FAN_TOTAL_DURATION += timedelta(seconds=run_time)
                CYCLE_COUNT += 1
                FAN_RUNNING = False
                FAN_RUNNING_TIME = timedelta(seconds=run_time)
                #  TODO: Saving limit multiple times
                if FAN_RUNNING_TIME > FAN_MAX_RUNTIME:
                    FAN_MAX_RUNTIME = FAN_RUNNING_TIME
                if FAN_RUNNING_TIME > FAN_LIMIT:
                    # TODO: Add FAN_LIMIT logic, maybe a method or function?
                    print("Fan limit exceeded")
                    logger.log(timestamp, 'WARN', 'SYSTEM', 'FAN',
                               f"Fan time limit exceeded: {FAN_LIMIT}%")
                    _fan_limit_exceeded()
                FAN_RUNNING_TIME = 0
                save_config()
                BONNETDisplay.display_text_center_with_border('Fan Stopped...')
                time.sleep(1)
                # Reset display back to prev lines
                BONNETDisplay.display_rows_center(BONNETDisplay.oled_lines, justification='left')
                time.sleep(.1)  # Adjust as needed
    if time.time() - last_page_changed  > 5 and current_page > 0:
        current_page = 0
        show_page(current_page)
# @print_elapsed_time
def task_external():
    global EXTERNAL_LOW_TEMP, EXTERNAL_HIGH_TEMP, EXTERNAL_HIGH_HUMIDITY, EXTERNAL_LOW_HUMIDITY, EXTERNAL_TEMP, EXTERNAL_HUMIDITY

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
    EXTERNAL_TEMP = externaloutput['temperature']
    EXTERNAL_HUMIDITY = externaloutput['humidity']
    if current_page == 0:
        BONNETDisplay.update_line(3, text=f"{EXTERNAL_HUMIDITY}% - {EXTERNAL_TEMP}°C", justification='left')
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
        lcd_lines[2] = f"Duration: {FAN_TOTAL_DURATION}s"
        lcd_lines[3] = f"Running - {str(FAN_RUNNING)}"
        lcd2004Display.display_four_rows_center(lcd_lines, justification='left')

def oled_display():
    global lcd_lines
    lcd_lines[0] = f"Int Max:{INTERNAL_HIGH_TEMP}C {INTERNAL_HIGH_HUMIDITY}%"
    lcd_lines[1] = f"Int Min:{INTERNAL_LOW_TEMP}C {INTERNAL_LOW_HUMIDITY}%"
    lcd_lines[2] = f"Ext Max:{EXTERNAL_HIGH_TEMP}C {EXTERNAL_HIGH_HUMIDITY}%"
    lcd_lines[3] = f"Ext Min:{EXTERNAL_LOW_TEMP}C {EXTERNAL_LOW_HUMIDITY}%"
    lcd2004Display.display_four_rows_center(lcd_lines, justification='left')

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

def display_default_page():
    # Render static data from global variables
    BONNETDisplay.display_rows_center(["Internal Sensor:", f"{INTERNAL_HUMIDITY}%" f" - {INTERNAL_TEMP}°C", "External Sensor:",
                                       f"{EXTERNAL_HUMIDITY}%" f" - {EXTERNAL_TEMP}°C", " "], 'white', 1.0, justification='left')


def display_fan_stats():
    BONNETDisplay.display_rows_center(["Fan Stats:", f"C {FAN_RUNNING_TIME}",f"M {FAN_MAX_RUNTIME}",
                                       f"T {FAN_TOTAL_DURATION}", " " ], 'white',1.0, justification='left')

def edit_humidity_set(button):
    global MIN_HUMIDITY, MAX_HUMIDITY, humidity_mode, humidity_selected, humidity_blink_state

    if humidity_mode == "selection":
        # In selection mode: toggle between 'max' and 'min' with U and D buttons
        if button.pin.number == BTN_U_PIN or button.pin.number == BTN_D_PIN:
            humidity_selected = "min" if humidity_selected == "max" else "max"
            display_set_humidity()

        # Enter edit mode when 'A' button is pressed
        elif button.pin.number == BTN_A_PIN:
            humidity_mode = "edit"
            humidity_blink_state = True
            display_set_humidity()

    elif humidity_mode == "edit":
        # In edit mode: adjust the selected humidity value with U and D buttons
        if button.pin.number == BTN_U_PIN:
            if humidity_selected == "max":
                MAX_HUMIDITY = round(MAX_HUMIDITY + 0.1, 1)
            else:
                MIN_HUMIDITY = round(MIN_HUMIDITY + 0.1, 1)
            display_set_humidity()

        elif button.pin.number == BTN_D_PIN:
            if humidity_selected == "max":
                MAX_HUMIDITY = round(MAX_HUMIDITY - 0.1, 1)
            else:
                MIN_HUMIDITY = round(MIN_HUMIDITY - 0.1, 1)
            display_set_humidity()

        # Save the value and exit edit mode when 'B' button is pressed
        elif button.pin.number == BTN_B_PIN:
            humidity_mode = "selection"
            humidity_blink_state = True
            display_set_humidity()

def display_set_humidity():
    BONNETDisplay.clear_screen()
    BONNETDisplay.display_text("Humidity Set", 10, 40)

    # Highlight selected values
    if humidity_selected == "max":
        max_color = "red" if humidity_blink_state or humidity_mode == "selection" else "black"
        min_color = "white"
    else:
        max_color = "white"
        min_color = "red" if humidity_blink_state or humidity_mode == "selection" else "black"

    # Display the values with corresponding highlighting
    BONNETDisplay.display_text("Max:", 10, 80)
    BONNETDisplay.display_text(f"{MAX_HUMIDITY:.1f}%", 100, 80, color_name=max_color)

    BONNETDisplay.display_text("Min:", 10, 120)
    BONNETDisplay.display_text(f"{MIN_HUMIDITY:.1f}%", 100, 120, color_name=min_color)

def display_internal_stats():
    # BONNETDisplay.display_text_center(page_3_data, color_name="yellow", brightness_factor=1.0)
    BONNETDisplay.display_rows_center(["Internal Stats:", f"Max Temp {INTERNAL_HIGH_TEMP}",
                                           f"Min Temp {INTERNAL_LOW_TEMP}", f"Max Hum {INTERNAL_HIGH_HUMIDITY}",
                                           f"Min Hum {INTERNAL_LOW_HUMIDITY}"], 'white',1.0, justification='left')

def display_external_stats():

    BONNETDisplay.display_rows_center(["External Stats:", f"Max Temp {EXTERNAL_HIGH_TEMP}",
                                       f"Min Temp {EXTERNAL_LOW_TEMP}", f"Max Hum {EXTERNAL_HIGH_HUMIDITY}",
                                       f"Min Hum {EXTERNAL_LOW_HUMIDITY}"], 'white',1.0, justification='left')

def show_page(page_index):
    global last_page_changed
    last_page_changed = time.time()
    if page_index == 0:
        display_default_page()
    elif page_index == 1:
        display_fan_stats()
    elif page_index == 2:
        display_internal_stats()
    elif page_index == 3:
        display_external_stats()
    elif page_index == 4:
        display_set_humidity()

def save_config():
    global MIN_HUMIDITY, MAX_HUMIDITY, INTERNAL_LOW_HUMIDITY, INTERNAL_HIGH_HUMIDITY
    global INTERNAL_HIGH_TEMP, INTERNAL_HIGH_HUMIDITY, EXTERNAL_LOW_TEMP, EXTERNAL_HIGH_TEMP
    global EXTERNAL_LOW_HUMIDITY, EXTERNAL_HIGH_HUMIDITY, EXTERNAL_LOW_TEMP, EXTERNAL_HIGH_TEMP
    global CYCLE_COUNT, FAN_TOTAL_DURATION, FAN_MAX_RUNTIME

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
    configManager.set_duration_config('total_cycle_duration', FAN_TOTAL_DURATION, 'LOG')
    configManager.set_duration_config('MAX_FAN_RUNTIME', FAN_MAX_RUNTIME, 'LOG')

def button_pressed_callback(button):
    global MIN_HUMIDITY, MAX_HUMIDITY, last_press_time, humidity_changed, mode, current_page, humidity_blink_state, humidity_mode
    now = time.time()

    if button.pin.number == BTN_L_PIN:
        # Navigate to previous page
        current_page -= 1
        if current_page < 0:
            current_page = total_pages - 1  # Wrap around to the last page
        humidity_mode = "selection"  # Reset humidity mode when changing page
    elif button.pin.number == BTN_R_PIN:
        # Navigate to next page
        current_page += 1
        if current_page >= total_pages:
            current_page = 0  # Wrap around to the first page
        humidity_mode = "selection"  # Reset humidity mode when changing pages
    elif button.pin.number == BTN_U_PIN:
        print("Up button pressed")
    elif button.pin.number == BTN_D_PIN:
        print("Down button pressed")
    elif button.pin.number == BTN_C_PIN:
        print("Center button pressed")
    elif button.pin.number == BTN_A_PIN:
        print("A button pressed")
    elif button.pin.number == BTN_B_PIN:
        print("B button pressed")
    else:
        print("Unknown button")
    
    show_page(current_page)
        
    if current_page == 4:
        edit_humidity_set(button)

def button_hold_callback(button):
    global MIN_HUMIDITY, MAX_HUMIDITY, last_press_time, humidity_changed, mode

def _fan_limit_exceeded():
    # TODO: Should this be a hard limit? Some way to change this maybe?
    # Cancel all the jobs
    schedule.clear()
    BONNETDisplay.display_text_center_with_border('FAN LIMIT EXCEEDED')
    lcd2004Display.display_text_with_border(['FAN LIMIT EXCEEDED'])
    fanController.set_fan_speed(0)
    save_config()
    while True:
        time.sleep(1)

def cleanup():
    # Want to add code here to update display, update log with run time etc
    print('Cleaning Up')
    try:
        BONNETDisplay.display_text_center_with_border('Shutting down...')
        if isDeviceDetected(statuses, 'LCD2004'):
            lcd2004Display.display_text_with_border(['Shutting down...'])
            lcd2004Display.clear()

        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO',
                   'System', 'System', "Shutting down...")
        # make sure fan is off
        fanController.set_fan_speed(0)
        time.sleep(3)
        BONNETDisplay.clear_screen()
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
    BTN_L_PIN = configManager.get_int_config('BTN_L_PIN')
    BTN_R_PIN = configManager.get_int_config('BTN_R_PIN')
    BTN_U_PIN = configManager.get_int_config('BTN_U_PIN')
    BTN_D_PIN = configManager.get_int_config('BTN_D_PIN')
    BTN_C_PIN = configManager.get_int_config('BTN_C_PIN')
    BTN_A_PIN = configManager.get_int_config('BTN_A_PIN')
    BTN_B_PIN = configManager.get_int_config('BTN_B_PIN')

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
    FAN_TOTAL_DURATION = configManager.get_duration_config('LOG', 'FAN_TOTAL_DURATION')
    FAN_MAX_RUNTIME = configManager.get_duration_config('LOG', 'FAN_MAX_RUNTIME')
    FAN_LIMIT = configManager.get_duration_config('DEFAULT', 'FAN_LIMIT')

    # Display configuration
    DISPLAY_ENABLED = configManager.get_boolean_config('DISPLAY_ENABLED')

    # Initialize current screen
    task_alternate_screens.current_screen = 1

    # Variables to manage button state and humidity values
    last_press_time = {'up': 0, 'dn': 0}
    last_page_changed = time.time()
    BUTTON_HOLD_TIME = 3
    humidity_changed = False
    mode = None
    INTERNAL_TEMP = 0
    INTERNAL_HUMIDITY = 0
    EXTERNAL_TEMP = 0
    EXTERNAL_HUMIDITY = 0

    # Global state variables
    humidity_mode = "selection"  # Can be 'selection' or 'edit'
    humidity_selected = "max"  # Can be 'max' or 'min'
    humidity_blink_state = True  # Used for blinking the value in edit mode

    # Variable to hold current page index
    current_page = 0
    total_pages = 5

    # GPIO setup using gpiozero for input buttons
    btn_lt = Button(BTN_L_PIN, pull_up=True, bounce_time=0.1, hold_time=BUTTON_HOLD_TIME)
    btn_rt = Button(BTN_R_PIN, pull_up=True, bounce_time=0.1, hold_time=BUTTON_HOLD_TIME)
    btn_up = Button(BTN_U_PIN, pull_up=True, bounce_time=0.1, hold_time=BUTTON_HOLD_TIME)
    btn_dn = Button(BTN_D_PIN, pull_up=True, bounce_time=0.1, hold_time=BUTTON_HOLD_TIME)
    btn_ctr = Button(BTN_C_PIN, pull_up=True, bounce_time=0.1, hold_time=BUTTON_HOLD_TIME)
    btn_a = Button(BTN_A_PIN, pull_up=True, bounce_time=0.1, hold_time=BUTTON_HOLD_TIME)
    btn_b = Button(BTN_B_PIN, pull_up=True, bounce_time=0.1, hold_time=BUTTON_HOLD_TIME)

    # Attach event handlers
    btn_lt.when_pressed = button_pressed_callback
    btn_rt.when_pressed = button_pressed_callback
    btn_up.when_pressed = button_pressed_callback
    btn_dn.when_pressed = button_pressed_callback
    btn_ctr.when_pressed = button_pressed_callback
    btn_a.when_pressed = button_pressed_callback
    btn_b.when_pressed = button_pressed_callback

    # Initialize lines
    oled_lines = [""] * 5  # For five line bonnet display...
    lcd_lines = [""] * 4  # For four line ssd1306_display...

    FAN_RUNNING = False
    FAN_RUNNING_TIME = 0
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
            # raise ValueError("Overall Status Failed")

        print ('Initializing LCD Display...')
        if isDeviceDetected(statuses, 'LCD2004'):
            lcd2004Display = LCD2004Display()
            lcd2004Display.clear()
            lcd2004Display.display_text_with_border(['Initializing...'])

        # Initialize displays...
        # Need to do this first so if there is an error cleanup can still work...
        print('Initializing Primary Display...')
        BONNET_display_config = DisplayConfig(font_path=FONT, font_size=FONTSIZE, border_size=BORDER)
        BONNETDisplay = BONNETDisplay(BONNET_display_config)

        # Display centered text
        BONNETDisplay.display_text_center("Initializing...")
        time.sleep(2)

        # Initialize to show the first page
        show_page(current_page)

        # Initialize fan controller
        print('Initializing fan controller...')
        fanController = EMC2101()

        time.sleep(2)
        internalsensor = Sensor('SHT41_Internal', 0x44)

        # sht30_sensor = Sensor('SHT30', 0x44)
        # print(sht30_sensor.sensor.relative_humidity, sht30_sensor.sensor.temperature)

        if isDeviceDetected(statuses, 'SHTC3'):
            externalsensor = Sensor('SHTC3', 0x70)
            externalprevious_output = {'temperature': 0, 'humidity': 0}

        # Initialize previous output values to None
        internalprevious_output = {'temperature': 0, 'humidity': 0}

        print("Internal Mode: ", internalsensor.sensor_mode())  # TODO: Figure out what mode is...
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

    except OSError as e:
        print("\nOS Error!", e)

    except NameError as e:
        print("\nName Error!",e)

    finally:
        cleanup()
