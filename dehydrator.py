
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
import threading

# Spinner frames to simulate rotation
spinner_frames = ['|', '/', '-', '\\']

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

def spinner():
    while running:
        if current_page == 0:
            for frame in spinner_frames:
                BONNETDisplay.display_text(text=frame,x_pos=100,y_pos=190,color_name="white",brightness_factor=1)
                time.sleep(0.2)  # Adjust speed of rotation (e.g., 0.2 seconds per frame)

# @print_elapsed_time
def task_internal():
    global INTERNAL_HIGH_TEMP, INTERNAL_HIGH_HUMIDITY, INTERNAL_LOW_TEMP, INTERNAL_LOW_HUMIDITY, \
        CYCLE_COUNT, FAN_TOTAL_DURATION, FAN_RUNNING, FAN_RUNNING_TIME, FAN_MAX_RUNTIME,\
        INTERNAL_TEMP, INTERNAL_HUMIDITY, current_page, EXTERNAL_TEMP

    if fanController.fan_engaged and current_page == 1:
        FAN_RUNNING_TIME = timedelta(seconds=(int(time.time() -  fanController.start_time)))
        # TODO: Update only the current time line...
        # display_fan_stats()

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    internaloutput = internalsensor.read_sensor()

    # Update the config file with stats
    new_high_humidity = max(INTERNAL_HIGH_HUMIDITY, internaloutput['humidity'])
    new_low_humidity = min(INTERNAL_LOW_HUMIDITY, internaloutput['humidity'])

    new_high_temp = max(INTERNAL_HIGH_TEMP, internaloutput['temperature'])
    new_low_temp = min(INTERNAL_LOW_TEMP, internaloutput['temperature'])

    # Check if any of the values changed
    log_changed = (
            new_high_humidity != INTERNAL_HIGH_HUMIDITY or
            new_low_humidity != INTERNAL_LOW_HUMIDITY or
            new_high_temp != INTERNAL_HIGH_TEMP or
            new_low_temp != INTERNAL_LOW_TEMP
    )

    # Update the variables if they changed
    if log_changed:
        INTERNAL_HIGH_HUMIDITY = new_high_humidity
        INTERNAL_LOW_HUMIDITY = new_low_humidity
        INTERNAL_HIGH_TEMP = new_high_temp
        INTERNAL_LOW_TEMP = new_low_temp
        save_config()

    def handle_fan_operation(started, stopped, run_time, action):
        global FAN_RUNNING, FAN_TOTAL_DURATION, CYCLE_COUNT  # Explicitly declare global variables
        """Handle fan start/stop operations, including logging, display updates, and timing."""
        if action == "start" and started:
            fanController.start_time = time.time()
            logger.log(timestamp, 'INFO', 'SYSTEM', 'FAN', f"Fan started, exceeded MAX humidity of {MAX_HUMIDITY}%")
            print(f"Fan started, exceeded set humidity of: {MAX_HUMIDITY}%")
            BONNETDisplay.display_text_center_with_border('Fan Started...')
            time.sleep(2)
            FAN_RUNNING = True
            show_page(current_page)
        elif action == "stop" and stopped:
            print(f"Fan stopped, passed MIN humidity of: {MIN_HUMIDITY}%")
            logger.log(timestamp, 'INFO', 'SYSTEM', 'FAN', f"Fan stopped, passed MIN humidity of: {MIN_HUMIDITY}%")
            logger.log(timestamp, 'INFO', 'SYSTEM', 'FAN', f"Fan run time: {str(timedelta(seconds=run_time))}")
            FAN_TOTAL_DURATION += timedelta(seconds=run_time)
            CYCLE_COUNT += 1
            FAN_RUNNING = False
            BONNETDisplay.display_text_center_with_border('Fan Stopped...')
            time.sleep(2)
            show_page(current_page)

        # Update maximum runtime and check limits
        fan_runtime_exceeded(run_time)

    def fan_runtime_exceeded(run_time):
        """Check if the fan runtime exceeds set limits and handle warnings."""
        global FAN_MAX_RUNTIME, FAN_RUNNING_TIME  # Explicitly declare global variables
        if run_time is None:
            FAN_RUNNING_TIME = timedelta(seconds=0)
        else:
            FAN_RUNNING_TIME = timedelta(seconds=int(run_time))

        if FAN_RUNNING_TIME > FAN_MAX_RUNTIME:
            FAN_MAX_RUNTIME = FAN_RUNNING_TIME
        if FAN_RUNNING_TIME > FAN_LIMIT:
            print("Fan limit exceeded")
            logger.log(timestamp, 'WARN', 'SYSTEM', 'FAN', f"Fan time limit exceeded: {FAN_LIMIT}")
            _fan_limit_exceeded()

    def update_internal_output_and_log():
        """Log internal sensor reading and update previous output values."""
        logger.log(timestamp, 'INFO', 'SENSORS', 'INTERNAL',
                   f"Temperature: {internaloutput['temperature']}C, Humidity: {internaloutput['humidity']}%")
        print("Internal Sensor Reading:", internaloutput)
        internalprevious_output['temperature'] = internaloutput['temperature']
        internalprevious_output['humidity'] = internaloutput['humidity']

    def update_current_page():
        """Update the default page display if needed."""
        if current_page == 0: # Default page
            if UOM == 'F':
                BONNETDisplay.display_text(text=f"{INTERNAL_HUMIDITY}% - {celsius_to_fahrenheit(INTERNAL_TEMP)}°F",
                                           x_pos=0,y_pos=63, color_name="white", brightness_factor=1.0)
                BONNETDisplay.display_text(text=f"{EXTERNAL_HUMIDITY}% - {celsius_to_fahrenheit(EXTERNAL_TEMP)}°F",
                                           x_pos=0,y_pos=159, color_name="white", brightness_factor=1.0)
            else:
                BONNETDisplay.display_text(text=f"{INTERNAL_HUMIDITY}% - {INTERNAL_TEMP}°C",
                                           x_pos=0,y_pos=63, color_name="white", brightness_factor=1.0)
                BONNETDisplay.display_text(text=f"{EXTERNAL_HUMIDITY}% - {EXTERNAL_TEMP}°C",
                                           x_pos=0,y_pos=159, color_name="white", brightness_factor=1.0)

        elif current_page == 1: # Fan Stats
            print("Fan running time:", FAN_RUNNING_TIME)
            BONNETDisplay.display_text(text=f"Current: {FAN_RUNNING_TIME}",
                                       x_pos=0, y_pos=63, color_name="white", brightness_factor=1.0)

    # Main block to handle sensor change and fan control
    INTERNAL_HUMIDITY = internaloutput['humidity']
    INTERNAL_TEMP = internaloutput['temperature']

    # Display the updated information on the current page if applicable
    update_current_page()

    # Handle fan start logic based on humidity thresholds
    if internaloutput['humidity'] > MAX_HUMIDITY:
        started, run_time = fanController.set_fan_speed(100)
        handle_fan_operation(started, False, run_time, "start")
    elif internaloutput['humidity'] < MIN_HUMIDITY:
        stopped, run_time = fanController.set_fan_speed(0)
        handle_fan_operation(False, stopped, run_time, "stop")

    if abs(internaloutput['humidity'] - internalprevious_output['humidity']) > 0.2:
        # Update log and internal values
        update_internal_output_and_log()

    if time.time() - last_page_changed  > 8 and (0 < current_page < 4):
        current_page = 0
        show_page(current_page)

# @print_elapsed_time
def task_ambient():
    global EXTERNAL_LOW_TEMP, EXTERNAL_HIGH_TEMP, EXTERNAL_HIGH_HUMIDITY, EXTERNAL_LOW_HUMIDITY, EXTERNAL_TEMP, EXTERNAL_HUMIDITY

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    externaloutput = externalsensor.read_sensor()

    # Calculate new high and low values
    new_high_humidity = max(EXTERNAL_HIGH_HUMIDITY, externaloutput['humidity'])
    new_low_humidity = min(EXTERNAL_LOW_HUMIDITY, externaloutput['humidity'])

    new_high_temp = max(EXTERNAL_HIGH_TEMP, externaloutput['temperature'])
    new_low_temp = min(EXTERNAL_LOW_TEMP, externaloutput['temperature'])

    # Check if any values changed
    log_changed = (
            new_high_humidity != EXTERNAL_HIGH_HUMIDITY or
            new_low_humidity != EXTERNAL_LOW_HUMIDITY or
            new_high_temp != EXTERNAL_HIGH_TEMP or
            new_low_temp != EXTERNAL_LOW_TEMP
    )

    # Update the variables if they changed
    if log_changed:
        EXTERNAL_HIGH_HUMIDITY = new_high_humidity
        EXTERNAL_LOW_HUMIDITY = new_low_humidity
        EXTERNAL_HIGH_TEMP = new_high_temp
        EXTERNAL_LOW_TEMP = new_low_temp
        save_config()

    # Log the sensor data every X seconds
    logger.log(timestamp, 'INFO', 'SENSORS', 'EXTERNAL',
               f"Temperature: {externaloutput['temperature']}C,"
               f" Humidity: {externaloutput['humidity']}%")

    # Update the global variables and print the reading
    externalprevious_output['temperature'] = externaloutput['temperature']
    externalprevious_output['humidity'] = externaloutput['humidity']
    EXTERNAL_TEMP = externaloutput['temperature']
    EXTERNAL_HUMIDITY = externaloutput['humidity']

    print("Ambient Sensor Reading:", externaloutput)

def task_display_reset():
    BONNETDisplay.reset_screen()
    display_default_page()

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
    schedule.every(ext_interval).minutes.do(task_ambient)
    schedule.every(5).minutes.do(task_display_reset)
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
    BONNETDisplay.display_rows_center(["Internal Sensor:", f"{INTERNAL_HUMIDITY}%" f" - {INTERNAL_TEMP}°C", "Ambient Sensor:",
                                       f"{EXTERNAL_HUMIDITY}%" f" - {EXTERNAL_TEMP}°C", " "],0, FAN_RUNNING,'white', 1.0, justification='left')

def display_fan_stats():
    if FAN_RUNNING_TIME == 0:
        BONNETDisplay.display_rows_center(["Fan Stats:", "Current: N/A", f"Max: {FAN_MAX_RUNTIME}",
                                           f"Total: {FAN_TOTAL_DURATION}", " "], 1, FAN_RUNNING,'white', 1.0, justification='left')
    else:
        BONNETDisplay.display_rows_center(["Fan Stats:", f"Current: {FAN_RUNNING_TIME}",f"Max: {FAN_MAX_RUNTIME}",
                                           f"Total: {FAN_TOTAL_DURATION}", " " ], 1,FAN_RUNNING,'white',1.0, justification='left')

def edit_humidity_set(button):
    global MIN_HUMIDITY, MAX_HUMIDITY, humidity_mode, humidity_selected, humidity_blink_state, max_color, min_color

    print("Running Edit Humidity")
    print(button.pin.number)
    if humidity_mode == "selection":
        # In selection mode: toggle between 'max' and 'min' with U and D buttons
        if button.pin.number == BTN_U_PIN or button.pin.number == BTN_D_PIN:
            humidity_selected = "min" if humidity_selected == "max" else "max"
            if humidity_selected == "max":
                max_color = "red" if humidity_blink_state or humidity_mode == "selection" else "black"
                min_color = "white"
            else:
                max_color = "white"
                min_color = "red" if humidity_blink_state or humidity_mode == "selection" else "black"
            BONNETDisplay.display_text(f"{MAX_HUMIDITY}%", 100, 80, color_name=max_color)
            BONNETDisplay.display_text(f"{MIN_HUMIDITY}%", 100, 120, color_name=min_color)

        # Enter edit mode when 'A' button is pressed
        elif button.pin.number == BTN_A_PIN:
            humidity_mode = "edit"
            humidity_blink_state = True

    elif humidity_mode == "edit":
        # In edit mode: adjust the selected humidity value with U and D buttons
        if button.pin.number == BTN_U_PIN:
            if humidity_selected == "max":
                MAX_HUMIDITY = round(MAX_HUMIDITY + 1, 1)
                BONNETDisplay.display_text(f"{MAX_HUMIDITY}%", 100, 80, color_name=max_color)
            else:
                MIN_HUMIDITY = round(MIN_HUMIDITY + 1, 1)
                BONNETDisplay.display_text(f"{MIN_HUMIDITY}%", 100, 120, color_name=min_color)

        elif button.pin.number == BTN_D_PIN:
            if humidity_selected == "max":
                MAX_HUMIDITY = round(MAX_HUMIDITY - 1, 1)
                BONNETDisplay.display_text(f"{MAX_HUMIDITY}%", 100, 80, color_name=max_color)
            else:
                MIN_HUMIDITY = round(MIN_HUMIDITY - 1, 1)
                BONNETDisplay.display_text(f"{MIN_HUMIDITY}%", 100, 120, color_name=min_color)

        # Save the value and exit edit mode when 'B' button is pressed
        elif button.pin.number == BTN_B_PIN:
            humidity_mode = "selection"
            humidity_blink_state = True

def display_set_humidity():
    BONNETDisplay.clear_screen()
    BONNETDisplay.display_text("Humidity Set", 1, 40)
    # Highlight selected values
    if humidity_selected == "max":
        max_color = "red" if humidity_blink_state or humidity_mode == "selection" else "black"
        min_color = "white"
    else:
        max_color = "white"
        min_color = "red" if humidity_blink_state or humidity_mode == "selection" else "black"

    # Display the values with corresponding highlighting
    BONNETDisplay.display_text("Max:", 1, 80, color_name="white")
    BONNETDisplay.display_text(f"{MAX_HUMIDITY}%", 100, 80, color_name=max_color)

    BONNETDisplay.display_text("Min:", 1, 120, color_name="white")
    BONNETDisplay.display_text(f"{MIN_HUMIDITY}%", 100, 120, color_name=min_color)

def display_internal_stats():
    # BONNETDisplay.display_text_center(page_3_data, color_name="yellow", brightness_factor=1.0)
    if UOM == 'F':
     BONNETDisplay.display_rows_center(["Internal Stats:", f"Max Temp {celsius_to_fahrenheit(INTERNAL_HIGH_TEMP)}F",
                                           f"Min Temp {celsius_to_fahrenheit(INTERNAL_LOW_TEMP)}F", f"Max Hum {INTERNAL_HIGH_HUMIDITY}",
                                           f"Min Hum {INTERNAL_LOW_HUMIDITY}"], 2, FAN_RUNNING,'white',1.0, justification='left')
    else:
        BONNETDisplay.display_rows_center(["Internal Stats:", f"Max Temp {INTERNAL_HIGH_TEMP}C",
                                           f"Min Temp {INTERNAL_LOW_TEMP}C", f"Max Hum {INTERNAL_HIGH_HUMIDITY}",
                                           f"Min Hum {INTERNAL_LOW_HUMIDITY}"], 2, FAN_RUNNING, 'white', 1.0,
                                          justification='left')


def display_external_stats():
    if UOM == 'F':
        BONNETDisplay.display_rows_center(["Ambient Stats:", f"Max Temp {celsius_to_fahrenheit(EXTERNAL_HIGH_TEMP)}",
                                           f"Min Temp {celsius_to_fahrenheit(EXTERNAL_LOW_TEMP)}", f"Max Hum {EXTERNAL_HIGH_HUMIDITY}",
                                           f"Min Hum {EXTERNAL_LOW_HUMIDITY}"], 3, FAN_RUNNING,'white',1.0, justification='left')
    else:
        BONNETDisplay.display_rows_center(["Ambient Stats:", f"Max Temp {EXTERNAL_HIGH_TEMP}",
                                           f"Min Temp {EXTERNAL_LOW_TEMP}", f"Max Hum {EXTERNAL_HIGH_HUMIDITY}",
                                           f"Min Hum {EXTERNAL_LOW_HUMIDITY}"], 3, FAN_RUNNING, 'white', 1.0,
                                          justification='left')


def draw_fan_limit():
    global selected_option, current_page
    current_page = 5
    BONNETDisplay.display_ok_clear("Fan Limit Exceeded",ok_text="OK", clear_text="CLEAR", color_name="white",
                                   brightness_factor=1.0, selected=selected_option)

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
    configManager.update_config('UOM', UOM)

def button_pressed_callback(button):
    global MIN_HUMIDITY, MAX_HUMIDITY, last_press_time, humidity_changed, mode, current_page, humidity_blink_state, \
        humidity_mode, FAN_LIMIT, selected_option
    print("Current starting page:", current_page)
    if button.pin.number == BTN_L_PIN:
        print("Button L pressed")
        if current_page == 5:
            selected_option = 1
            draw_fan_limit()
        else:
            current_page -= 1
            if current_page < 0:
                # Wrap around to the last page accounting for config page
                current_page = total_pages - 1
            humidity_mode = "selection"  # Reset humidity mode when changing page
    elif button.pin.number == BTN_R_PIN:
        print("Button R Pressed")
        if current_page == 5:
            selected_option = 2
            draw_fan_limit()
        else:
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
        if current_page == 5:
            if selected_option == 1: # OK Selected
                schedule.clear()
                cleanup()
                exit()
            elif selected_option == 2: # CLEAR Selected
                FAN_LIMIT *= 2  # Double the fan limit
                current_page = 0  # Return to page 0
                schedule_tasks()
    elif button.pin.number == BTN_B_PIN:
         print("B button pressed")
    else:
        print("Unknown button")

    print("Selected page: ", current_page)
    if current_page < 5:
        show_page(current_page)
        
    if current_page == 4:
        edit_humidity_set(button)

def button_hold_callback(button):
    global MIN_HUMIDITY, MAX_HUMIDITY, last_press_time, humidity_changed, mode, current_page
    if button.pin.number == BTN_B_PIN:
        print("Button B held...")
        BONNETDisplay.reset_screen()
        current_page = 0
        display_default_page()

def _fan_limit_exceeded():
    global current_page
    schedule.clear()
    current_page = 5
    BONNETDisplay.display_text_center_with_border('FAN LIMIT EXCEEDED')
    time.sleep(3)
    if isDeviceDetected(statuses, 'LCD2004'):
        lcd2004Display = LCD2004Display()
        lcd2004Display.clear()
        lcd2004Display.display_text_with_border(['FAN LIMIT EXCEEDED'])
    draw_fan_limit()
    fanController.set_fan_speed(0)
    save_config()

def cleanup():
    # Want to add code here to update display, update log with run time etc
    global running
    print('Cleaning Up')
    running = False
    spinner_thread.join()  # Wait for the spinner to finish
    try:
        BONNETDisplay.display_text_center_with_border('Shutting down...')
        if isDeviceDetected(statuses, 'LCD2004'):
            lcd2004Display.display_text_with_border(['Shutting down...'])
            lcd2004Display.clear()

        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO',
                   'System', 'System', "Shutting down...")
        # make sure fan is off
        fanController.set_fan_speed(0)
        time.sleep(1)
        BONNETDisplay.clear_screen()
    except NameError:
        print('LCD Not Defined')
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'FATAL',
                   'System', 'System', "No display available...")
    finally:
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'FATAL',
                   'System', 'System', "System Shutting down..")
    exit()

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
    UOM = configManager.get_config('UOM')

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
    current_page = 0
    total_pages = 5
    selected_option = 1
    max_color = "white"
    min_color = "white"

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
    btn_b.when_held = button_hold_callback

    # Initialize lines
    oled_lines = [""] * 5  # For five line bonnet display...
    lcd_lines = [""] * 4  # For four line ssd1306_display...

    FAN_RUNNING = False
    FAN_RUNNING_TIME = 0

    running = True
    spinner_thread = threading.Thread(target=spinner)

    # Start the spinner in the background
    spinner_thread.start()

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
        task_ambient()
        if DISPLAY_ENABLED:
            lcd_display(1)

        run_scheduler()

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected!")
    except ValueError as e:
        print("\nValue Error!",e)
    except OSError as e:
        print("\nOS Error!", e)
    except NameError as e:
        print("\nName Error!",e)
    finally:
        cleanup()
