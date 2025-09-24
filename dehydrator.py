import schedule
import time
from datetime import timedelta
from config_manager import ConfigManager
from logger import Logger as Log
from display import BONNETDisplay, DisplayConfig
from oled_display_manager import OLEDDisplayManager, Screen
from gpiozero import Button
from sensor import Sensor
from fan_controller import EMC2101Controller
import threading
from notification_manager import NotificationManager
from system_monitor import get_system_stats
import signal
import os
from safei2c import SafeI2C
from system_status import SystemStatus
from system_state import SystemState

print("Dehydrator main loaded")

# Spinner frames to simulate rotation
spinner_frames = ['▖', '▘', '▝', '▗']
# Get configuration items
system_state = SystemState()
configManager = ConfigManager('config.ini', system_state)
configManager.load_config()

# Initialize logging system
logger = Log(system_state.LOGFILE, system_state.MAX_LOG_SIZE, system_state.MAX_ARCHIVE_SIZE)

notifier = NotificationManager(
    logger = logger,
    provider="yahoo",                       # "yahoo" | "icloud" | "apple"
    email="imaplt@yahoo.com",
    password="",                            # app password recommended
    recipients=["chris.auron@gmail.com"],
    retry_days=7,                           # configurable retention
    poll_interval=300,                      # worker checks every 5 min
    auto_start=True                         # background thread starts automatically
)

def get_next_frame():
    global current_frame_index
    # Get the current frame
    frame = spinner_frames[current_frame_index]

    # Increment the index to get the next frame on the next call
    current_frame_index = (current_frame_index + 1) % len(spinner_frames)

    return frame

# Initialize the lock
lock = threading.Lock()
system_state.shutdown_timer = None
systemstatus = SystemStatus()

def celsius_to_fahrenheit(celsius):
    fahrenheit = (celsius * 9/5) + 32
    return round(fahrenheit, 1)

def sensor(stop_event):
    while running and not stop_event.is_set():
        try:
            ### BEGIN Internal Sensor Code block
            internaloutput = internalsensor.read_sensor()
            internaloutput['temperature'] = celsius_to_fahrenheit(internaloutput['temperature'])

            # Main block to handle sensor change and fan control
            system_state.INTERNAL_HUMIDITY = internaloutput['humidity']
            system_state.INTERNAL_TEMP = internaloutput['temperature']

            if abs(system_state.INTERNAL_HUMIDITY - system_state.INTERNAL_PREVIOUS_HUMIDITY) > 0.3:
                """Log internal sensor reading and update previous output values."""
                logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO', 'SENSORS', 'INTERNAL',
                           f"Temperature: {internaloutput['temperature']}F, Humidity: {internaloutput['humidity']}%")
                system_state.INTERNAL_PREVIOUS_HUMIDITY = system_state.INTERNAL_HUMIDITY

            # Update the config file with stats
            new_high_humidity = max(system_state.INTERNAL_HIGH_HUMIDITY, internaloutput['humidity'])
            new_low_humidity = min(system_state.INTERNAL_LOW_HUMIDITY, internaloutput['humidity'])

            new_high_temp = max(system_state.INTERNAL_HIGH_TEMP, internaloutput['temperature'])
            new_low_temp = min(system_state.INTERNAL_LOW_TEMP, internaloutput['temperature'])

            # Check if any of the values changed
            log_changed = (
                    new_high_humidity != system_state.INTERNAL_HIGH_HUMIDITY or
                    new_low_humidity != system_state.INTERNAL_LOW_HUMIDITY or
                    new_high_temp != system_state.INTERNAL_HIGH_TEMP or
                    new_low_temp != system_state.INTERNAL_LOW_TEMP
            )

            # Update the variables if they changed
            if log_changed:
                system_state.INTERNAL_HIGH_HUMIDITY = new_high_humidity
                system_state.INTERNAL_LOW_HUMIDITY = new_low_humidity
                system_state.INTERNAL_HIGH_TEMP = new_high_temp
                system_state.INTERNAL_LOW_TEMP = new_low_temp
                save_config()

            ambient_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) # type: ignore

            ### BEGIN EXTERNAL Sensor Code block
            externaloutput = externalsensor.read_sensor()
            externaloutput['temperature'] = celsius_to_fahrenheit(externaloutput['temperature'])

            # Calculate new high and low values
            new_high_humidity = max(system_state.EXTERNAL_HIGH_HUMIDITY, externaloutput['humidity'])
            new_low_humidity = min(system_state.EXTERNAL_LOW_HUMIDITY, externaloutput['humidity'])

            new_high_temp = max(system_state.EXTERNAL_HIGH_TEMP, externaloutput['temperature'])
            new_low_temp = min(system_state.EXTERNAL_LOW_TEMP, externaloutput['temperature'])

            # Check if any values changed
            log_changed = (
                    new_high_humidity != system_state.EXTERNAL_HIGH_HUMIDITY or
                    new_low_humidity != system_state.EXTERNAL_LOW_HUMIDITY or
                    new_high_temp != system_state.EXTERNAL_HIGH_TEMP or
                    new_low_temp != system_state.EXTERNAL_LOW_TEMP
            )

            # Update the variables if they changed
            if log_changed:
                system_state.EXTERNAL_HIGH_HUMIDITY = new_high_humidity
                system_state.EXTERNAL_LOW_HUMIDITY = new_low_humidity
                system_state.EXTERNAL_HIGH_TEMP = new_high_temp
                system_state.EXTERNAL_LOW_TEMP = new_low_temp
                save_config()

            if abs(system_state.EXTERNAL_HUMIDITY - system_state.EXTERNAL_PREVIOUS_HUMIDITY) > 0.3:
                """Log external sensor reading and update previous output values."""
                logger.log(ambient_timestamp, 'INFO', 'SENSORS', 'EXTERNAL',
                           f"Temperature: {externaloutput['temperature']}F,"
                           f" Humidity: {externaloutput['humidity']}%")
                system_state.EXTERNAL_PREVIOUS_HUMIDITY = system_state.EXTERNAL_HUMIDITY

            # Update the global variables and print the reading
            system_state.EXTERNAL_TEMP = externaloutput['temperature']
            system_state.EXTERNAL_HUMIDITY = externaloutput['humidity']

            ### BEGIN AMBIENT Sensor Code block
            ambientoutput = ambientsensor.read_sensor()
            ambientoutput['temperature'] = celsius_to_fahrenheit(ambientoutput['temperature'])

            # Calculate new high and low values
            new_high_humidity = max(system_state.AMBIENT_HIGH_HUMIDITY, ambientoutput['humidity'])
            new_low_humidity = min(system_state.AMBIENT_LOW_HUMIDITY, ambientoutput['humidity'])

            new_high_temp = max(system_state.AMBIENT_HIGH_TEMP, ambientoutput['temperature'])
            new_low_temp = min(system_state.AMBIENT_LOW_TEMP, ambientoutput['temperature'])

            # Check if any values changed
            log_changed = (
                    new_high_humidity != system_state.AMBIENT_HIGH_HUMIDITY or
                    new_low_humidity != system_state.AMBIENT_LOW_HUMIDITY or
                    new_high_temp != system_state.AMBIENT_HIGH_TEMP or
                    new_low_temp != system_state.AMBIENT_LOW_TEMP
            )

            # Update the variables if they changed
            if log_changed:
                system_state.AMBIENT_HIGH_HUMIDITY = new_high_humidity
                system_state.AMBIENT_LOW_HUMIDITY = new_low_humidity
                system_state.AMBIENT_HIGH_TEMP = new_high_temp
                system_state.AMBIENT_LOW_TEMP = new_low_temp
                save_config()

            if abs(system_state.AMBIENT_HUMIDITY - system_state.AMBIENT_PREVIOUS_HUMIDITY) > 0.3:
                """Log ambient sensor reading and update previous output values."""
                logger.log(ambient_timestamp, 'INFO', 'SENSORS', 'AMBIENT',
                           f"Temperature: {ambientoutput['temperature']}F,"
                           f" Humidity: {ambientoutput['humidity']}%")
                system_state.AMBIENT_PREVIOUS_HUMIDITY = system_state.AMBIENT_HUMIDITY

            # Update the global variables and print the reading
            system_state.AMBIENT_TEMP = ambientoutput['temperature']
            system_state.AMBIENT_HUMIDITY = ambientoutput['humidity']


        except Exception as e:
            logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'WARN', 'SYSTEM', 'SENSOR',
                       "Sensor thread error: {}".format(e))
            print(f"Sensor thread error: {e}")
            cleanup()

def task_update():
    task_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    def handle_fan_operation(fan_started, fan_stopped, run_time, action):
        """Handle fan start/stop operations, including logging, display updates, and timing."""
        if action == "start" and fan_started:
            fanController.start_time = time.time()
            logger.log(task_timestamp, 'INFO', 'SYSTEM', 'FAN', f"Fan started, exceeded MAX humidity of {system_state.MAX_HUMIDITY}%")
            print(f"Fan started, exceeded set humidity of: {system_state.MAX_HUMIDITY}%")
            display_manager.switch_image(Screen.FAN_START)
            display_manager.display_current_image(BONNETDisplay.disp)
            system_state.FAN_RUNNING = True
            system_state.CYCLE_COUNT += 1
            update_stats()
            time.sleep(2)
            show_page(system_state.current_page)
        elif action == "stop" and fan_stopped:
            print(f"Fan stopped, passed MIN humidity of: {system_state.MIN_HUMIDITY}%")
            logger.log(task_timestamp, 'INFO', 'SYSTEM', 'FAN', f"Fan stopped, passed MIN humidity of: {system_state.MIN_HUMIDITY}%")
            logger.log(task_timestamp, 'INFO', 'SYSTEM', 'FAN', f"Fan run time: {str(timedelta(seconds=run_time))}")
            system_state.FAN_TOTAL_DURATION += timedelta(seconds=int(run_time))
            print(f"Fab Total Duration: {str(timedelta(seconds=run_time))}")
            system_state.FAN_RUNNING = False
            display_manager.switch_image(Screen.FAN_STOP)
            display_manager.display_current_image(BONNETDisplay.disp)
            update_stats()
            save_config()
            time.sleep(2)
            show_page(system_state.current_page)

    def fan_runtime_exceeded(run_time):
        """Check if the fan runtime exceeds set limits and handle warnings."""
        if run_time is None:
            system_state.FAN_RUNNING_TIME = timedelta(seconds=0)
        else:
            system_state.FAN_RUNNING_TIME = timedelta(seconds=int(run_time))

        if system_state.FAN_RUNNING_TIME > system_state.FAN_MAX_RUNTIME:
            system_state.FAN_MAX_RUNTIME = system_state.FAN_RUNNING_TIME
        if system_state.FAN_RUNNING_TIME > system_state.FAN_LIMIT:
            print("Fan limit exceeded")
            logger.log( time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'WARN', 'SYSTEM',
                        'FAN', f"Fan time limit exceeded: {system_state.FAN_LIMIT}")
            _fan_limit_exceeded()

    def update_current_page():
        """Update the default page display if needed."""
        if system_state.current_page == Screen.DEFAULT.index:
            with lock:
                BONNETDisplay.display_text(text=f"{system_state.INTERNAL_HUMIDITY}% - {system_state.INTERNAL_TEMP}°F",
                                           x_pos=6,y_pos=32, color_name="white", brightness_factor=1.0)
                BONNETDisplay.display_text(text=f"{system_state.EXTERNAL_HUMIDITY}% - {system_state.EXTERNAL_TEMP}°F",
                                           x_pos=6,y_pos=96, color_name="white", brightness_factor=1.0)
                BONNETDisplay.display_text(text=f"{system_state.AMBIENT_HUMIDITY}% - {system_state.AMBIENT_TEMP}°F",
                                           x_pos=6, y_pos=160, color_name="white", brightness_factor=1.0)

                frame = get_next_frame()
                BONNETDisplay.display_text(text=frame, x_pos=190, y_pos=190, color_name="white", brightness_factor=1)

    # Handle fan start logic based on humidity thresholds
    if system_state.INTERNAL_HUMIDITY > system_state.MAX_HUMIDITY:
        started, run_time = fanController.set_fan_speed(100)
        print(f"Started fan run time: {str(run_time)}")
        handle_fan_operation(started, False, run_time, "start")
    elif system_state.INTERNAL_HUMIDITY < system_state.MIN_HUMIDITY:
        stopped, run_time = fanController.set_fan_speed(0)
        handle_fan_operation(False, stopped, run_time, "stop")

    if fanController.fan_engaged:
        fan_runtime_exceeded(int(time.time() -  fanController.start_time))
        update_stats()

    if system_state.page_changed and system_state.current_page < 6:
        system_state.page_changed = False
        show_page(system_state.current_page)

    # Display the updated information on the current page if applicable
    update_current_page()

    if time.time() - last_page_changed  > 8 and (0 < system_state.current_page < 7):
        system_state.current_page = Screen.DEFAULT.index
        show_page(system_state.current_page)

def send_status(message="Status"):
    #TODO: Update the code for below
    status_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    current_status = f"{message} as of: {status_timestamp}\n"
    current_status += f"Overall: {overall_status}.\n".upper()
    for s in statuses:
        current_status += f"{s}\n"
    current_status += f"{system_stats}\n"
    startup_stats = get_system_stats(system_state)
    current_status += (f"CPU: {startup_stats['cpu_percent']}%, "
                    f"Mem: {startup_stats['memory_percent']}% ({startup_stats['memory_used_mb']}MB), "
                    f"Disk Free: {startup_stats['disk_free_gb']}GB, "
                    f"Temp: {celsius_to_fahrenheit(startup_stats['cpu_temp'])}°F\n")

    current_status += f"Logs: {startup_stats['logs']}\n"
    for sensor, stat in startup_stats["sensors"].items():
        current_status += f"{sensor.capitalize()}: {stat}\n"

    # you can add sensor readings too
    notifier.send_status(body=current_status, subject=message)

def send_daily_log():
    log_file = "log.csv"  # or however you track archived logs
    notifier.send_log(log_file)

def _cycle_fan():
    if not system_state.FAN_RUNNING:
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                   'INFO', 'SYSTEM', 'FAN', "Fan Cycle Started...")
        print("Fan Cycle Started...")
        fanController.set_fan_speed(100)
        time.sleep(system_state.FAN_DURATION)
        fanController.set_fan_speed(0)
    else:
        print("Fan Cycle Skipped...")
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                   'INFO', 'SYSTEM', 'FAN', "Fan running, skipping fan cycle...")

def log_system_status():
    global system_stats
    log_path = os.path.expanduser("~/dehydrator/Aircraft-Dehydrator")
    stats = get_system_stats(log_dir=log_path)
    if "error" in stats:
        print(f"System monitor error: {stats['error']}")
        log_line = f"System monitor error: {stats['error']}"
        logger.log( time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'WARN', 'SYSTEM', 'MONITOR', log_line)
    else:
        log_line = (f"CPU: {stats['cpu_percent']}%, "
                    f"Mem: {stats['memory_percent']}% ({stats['memory_used_mb']}MB), "
                    f"Disk Free: {stats['disk_free_gb']}GB, "
                    f"Temp: {celsius_to_fahrenheit(stats['cpu_temp'])}°F")
        logger.log( time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO', 'SYSTEM', 'MONITOR', log_line)
        logger.log( time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO', 'SYSTEM', 'MONITOR', f"Logs: {stats['logs']}")
        print(f"Sensors: {stats['sensors']}")
        for sensor, stat in stats["sensors"].items():
            logger.log( time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO', 'SYSTEM', 'MONITOR', f"{sensor.capitalize()}: {stat}")

        # you can also write to your output.log or CSV here
    system_stats = log_line

def schedule_tasks(int_interval=1, fan_interval=10, system_interval=10):
    schedule.every(int_interval).seconds.do(task_update)
    schedule.every().day.at("09:00").do(send_status, message="Daily Status")
    schedule.every().day.at("09:30").do(send_status, message="Daily Status")
    schedule.every().day.at("10:00").do(send_status, message="Daily Status")
    schedule.every().day.at("20:00").do(send_status, message="Daily Status")
    schedule.every().day.at("21:00").do(send_daily_log)
    schedule.every(fan_interval).minutes.do(_cycle_fan)
    schedule.every(system_interval).minutes.do(log_system_status)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(.1)

def heat_sensor():
    # TODO: Add code to heat sensors when the humidity gets high. Only applies to SHT4X series sensors
    print("Heating External sensor...")
    externalsensor.heat_sensor()
    logger.log(timestamp, 'INFO', 'SYSTEM', 'AMBIENT', "Heating External sensor...")

    print("Heating Internal sensor...")
    internalsensor.heat_sensor()
    logger.log(timestamp, 'INFO', 'SYSTEM', 'INTERNAL', "Heating Internal sensor...")

def read_installed_devices(config):
    devices = config.get_config('installed_devices').split(',')
    devices = [device.strip() for device in devices]  # Remove any extra whitespace
    return devices

def display_default_page():
    # Render static data from global variables
    BONNETDisplay.display_rows_top(["Internal Sensor:", f"system_state.{INTERNAL_HUMIDITY}%" f" - {system_state.INTERNAL_TEMP}°F",
                                       "External Sensor:", f"{system_state.EXTERNAL_HUMIDITY}%" f" - {system_state.EXTERNAL_TEMP}°F",
                                       "Ambient Sensor:", f"{system_state.AMBIENT_HUMIDITY}%" f" - {system_state.AMBIENT_TEMP}°F"],
                                      0, system_state.FAN_RUNNING,'white', 1.0, justification='left')

def edit_humidity_set(button):
    print("Running Edit Humidity")
    print(button.pin.number)
    if system_state.humidity_mode == "selection":
        # In selection mode: toggle between 'max' and 'min' with U and D buttons
        if button.pin.number == system_state.BTN_U_PIN or button.pin.number == system_state.BTN_D_PIN:
            humidity_selected = "min" if system_state.humidity_selected == "max" else "max"
            if humidity_selected == "max":
                max_color = "red" if system_state.humidity_blink_state or system_state.humidity_mode == "selection" else "black"
                min_color = "white"
            else:
                max_color = "white"
                min_color = "red" if system_state.humidity_blink_state or system_state.humidity_mode == "selection" else "black"
            BONNETDisplay.display_text(f"{system_state.MAX_HUMIDITY}%", 100, 80, color_name=max_color)
            BONNETDisplay.display_text(f"{system_state.MIN_HUMIDITY}%", 100, 120, color_name=min_color)

        # Enter edit mode when 'A' button is pressed
        elif button.pin.number == system_state.BTN_A_PIN:
            system_state.humidity_mode = "edit"
            system_state.humidity_blink_state = True

    elif system_state.humidity_mode == "edit":
        # In edit mode: adjust the selected humidity value with U and D buttons
        if button.pin.number == system_state.BTN_U_PIN:
            if system_state.humidity_selected == "max":
                system_state.MAX_HUMIDITY = round(system_state.MAX_HUMIDITY + 1, 1)
                BONNETDisplay.display_text(f"{system_state.MAX_HUMIDITY}%", 100, 80, color_name=system_state.max_color)
            else:
                system_state.MIN_HUMIDITY = round(system_state.MIN_HUMIDITY + 1, 1)
                BONNETDisplay.display_text(f"{system_state.MIN_HUMIDITY}%", 100, 120, color_name=system_state.min_color)

        elif button.pin.number == system_state.BTN_D_PIN:
            if system_state.humidity_selected == "max":
                system_state.MAX_HUMIDITY = round(system_state.MAX_HUMIDITY - 1, 1)
                BONNETDisplay.display_text(f"{system_state.MAX_HUMIDITY}%", 100, 80, color_name=system_state.max_color)
            else:
                system_state.MIN_HUMIDITY = round(system_state.MIN_HUMIDITY - 1, 1)
                BONNETDisplay.display_text(f"{system_state.MIN_HUMIDITY}%", 100, 120, color_name=system_state.min_color)

        # Save the value and exit edit mode when 'B' button is pressed
        elif button.pin.number == system_state.BTN_B_PIN:
            system_state.humidity_mode = "selection"
            system_state.humidity_blink_state = True

def display_set_humidity():
    BONNETDisplay.clear_screen()
    BONNETDisplay.display_text("Humidity Set", 1, 40)
    # Highlight selected values
    if system_state.humidity_selected == "max":
        system_state.max_color = "red" if system_state.humidity_blink_state or system_state.humidity_mode == "selection" else "black"
        system_state.min_color = "white"
    else:
        system_state.max_color = "white"
        system_state.min_color = "red" if system_state.humidity_blink_state or system_state.humidity_mode == "selection" else "black"

    # Display the values with corresponding highlighting
    BONNETDisplay.display_text("Max:", 1, 80, color_name="white")
    BONNETDisplay.display_text(f"{system_state.MAX_HUMIDITY}%", 100, 80, color_name=system_state.max_color)

    BONNETDisplay.display_text("Min:", 1, 120, color_name="white")
    BONNETDisplay.display_text(f"{system_state.MIN_HUMIDITY}%", 100, 120, color_name=system_state.min_color)

def display_stats_reset():
    system_state.current_page = Screen.RESET.index
    BONNETDisplay.display_ok_clear("Stats Reset",ok_text="OK", clear_text="CANCEL", color_name="white",
                                   brightness_factor=1.0, selected=system_state.selected_option)

def update_stats():
    internal_max_temp = INTERNAL_HIGH_TEMP
    external_max_temp = EXTERNAL_HIGH_TEMP
    ambient_max_temp = AMBIENT_HIGH_TEMP
    internal_min_temp = INTERNAL_LOW_TEMP
    external_min_temp = EXTERNAL_LOW_TEMP
    ambient_min_temp = AMBIENT_LOW_TEMP

    display_manager.update_internal_screen(texts=["Internal Stats:", f"Max Temp {internal_max_temp}F",
                                           f"Min Temp {internal_min_temp}F", f"Max Hum {system_state.INTERNAL_HIGH_HUMIDITY}",
                                           f"Min Hum {system_state.INTERNAL_LOW_HUMIDITY}"])

    display_manager.update_external_screen(texts=["External Stats:", f"Max Temp {external_max_temp}F",
                                                  f"Min Temp {external_min_temp}F", f"Max Hum {system_state.EXTERNAL_HIGH_HUMIDITY}",
                                                  f"Min Hum {system_state.EXTERNAL_LOW_HUMIDITY}"])

    display_manager.update_ambient_screen(texts=["Ambient Stats:", f"Max Temp {ambient_max_temp}F",
                                           f"Min Temp {ambient_min_temp}F", f"Max Hum {system_state.EXTERNAL_HIGH_HUMIDITY}",
                                           f"Min Hum {system_state.EXTERNAL_LOW_HUMIDITY}"])

    display_manager.update_fan_screen(texts=["Fan Stats:", f"Current: {system_state.FAN_RUNNING_TIME}", f"Max: {system_state.FAN_MAX_RUNTIME}",
                                             f"Total: {system_state.FAN_TOTAL_DURATION}", f"Cycles: {system_state.CYCLE_COUNT} "])

def draw_fan_limit():
    system_state.current_page = 6
    BONNETDisplay.display_ok_clear("Fan Limit Exceeded",ok_text="OK", clear_text="CLEAR", color_name="white",
                                   brightness_factor=1.0, selected=system_state.selected_option)

def show_page(page_index):
    system_state.last_page_changed = time.time()
    system_state.current_page = page_index
    if page_index == Screen.DEFAULT.index:
        display_default_page()
    elif page_index == Screen.FAN.index:
        display_manager.switch_image(Screen.FAN)
        display_manager.display_current_image(BONNETDisplay.disp)
    elif page_index == Screen.INTERNAL.index:
        display_manager.switch_image(Screen.INTERNAL)
        display_manager.display_current_image(BONNETDisplay.disp)
    elif page_index == Screen.EXTERNAL.index:
        display_manager.switch_image(Screen.EXTERNAL)
        display_manager.display_current_image(BONNETDisplay.disp)
    elif page_index == Screen.AMBIENT.index:
        display_manager.switch_image(Screen.AMBIENT)
        display_manager.display_current_image(BONNETDisplay.disp)
    elif page_index == 5:
        display_set_humidity()
    elif page_index == 6:
        display_stats_reset()

def button_pressed_callback(button):

    if system_state.shutdown_timer:  # noinspection PyUnreachableCode
        system_state.shutdown_timer.cancel() # type: ignore
        system_state.shutdown_timer = None

    if button.pin.number == system_state.BTN_L_PIN:
        print("Button L pressed")
        if system_state.current_page == Screen.FAN_LIMIT.index:
            system_state.selected_option = 1
            draw_fan_limit()
        else:
            system_state.current_page -= 1
            if system_state.current_page < 0:
                # Wrap around to the last page accounting for config page
                system_state.current_page = system_state.total_pages - 1
            system_state.page_changed = True
            system_state.humidity_mode = "selection"  # Reset humidity mode when changing page
    elif button.pin.number == system_state.BTN_R_PIN:
        print("Button R Pressed")
        if system_state.current_page == Screen.FAN_LIMIT.index:
            system_state.selected_option = 2
            draw_fan_limit()
        else:
            system_state.current_page += 1
            if system_state.current_page >= system_state.total_pages:
                system_state.current_page = Screen.DEFAULT.index  # Wrap around to the first page
            system_state.page_changed = True
            system_state.humidity_mode = "selection"  # Reset humidity mode when changing pages
    elif button.pin.number == system_state.BTN_U_PIN:
        print("Up button pressed")
    elif button.pin.number == system_state.BTN_D_PIN:
        print("Down button pressed")
    elif button.pin.number == system_state.BTN_C_PIN:
        print("Center button pressed")
        cleanup()
        os.system("sudo shutdown -h now")
    elif button.pin.number == system_state.BTN_A_PIN:
        print("A button pressed")
        if system_state.current_page == Screen.FAN_LIMIT.index :
            if system_state.selected_option == 1: # OK Selected
                schedule.clear()
                cleanup()
                raise SystemExit
            elif system_state.selected_option == 2: # CLEAR Selected
                system_state.FAN_LIMIT *= 2  # Double the fan limit
                system_state.fan_limit_exceeded_count += 1  # reset counter
                system_state.current_page = Screen.DEFAULT.index  # Return to page 0
                schedule_tasks()
        elif system_state.current_page == Screen.RESET.index:
            if system_state.selected_option == 1: # OK Selected
                stats_reset()
                save_config()
            elif system_state.selected_option == 2: # CANCEL Selected
                system_state.current_page = Screen.DEFAULT.index  # Return to page 0
    elif button.pin.number == system_state.BTN_B_PIN:
         print("B button pressed")
    else:
        print("Unknown button")

def button_hold_callback(button):
    if button.pin.number == system_state.BTN_B_PIN:
        print("Button B held...")
        BONNETDisplay.reset_screen()
        system_state. current_page = 0
        display_default_page()

def auto_shutdown():
    # Called if nobody presses a button in time
    system_state.FAN_LIMIT *= 2  # Double the fan limit
    system_state.current_page = Screen.DEFAULT.index  # Return to page 0
    schedule_tasks()

def _fan_limit_exceeded():
    system_state.fan_limit_exceeded_count += 1
    schedule.clear()
    system_state.current_page = 5
    print("Fan limit exceeded too many times. Shutting down.")
    if system_state.fan_limit_exceeded_count >= system_state.MAX_EXCEEDED_ATTEMPTS:
        # Too many repeats — force shutdown
        print("Fan limit exceeded too many times. Shutting down.")
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'ERROR', 'SYSTEM', 'FAN',
                   "Fan limit exceeded too many times. Shutting down.")
        fanController.set_fan_speed(0)
        save_config()
        cleanup()
        raise SystemExit
    # Display fan limit exceeded banner
    display_manager.switch_image(Screen.FAN_LIMIT)
    display_manager.display_current_image(BONNETDisplay.disp)
    time.sleep(3) # Display it for three seconds
    # Create the fan limit screen
    draw_fan_limit()
    # Set the fan speed to 0 RPM
    fanController.set_fan_speed(0)
    # Save any config changes
    save_config()
    # Start auto-shutdown timer (e.g., 30 seconds)
    system_state.shutdown_timer = threading.Timer(system_state.FAN_LIMIT_TIMEOUT.total_seconds(), auto_shutdown)
    system_state.shutdown_timer.start()

def handle_shutdown(signum):
    print(f"\nSignal {signum} received, shutting down...")
    logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'WARN', 'SYSTEM', 'SYSTEM',
               f"Signal {signum} received, shutting down...")
    raise KeyboardInterrupt

def stats_reset():
    system_state.CYCLE_COUNT = system_state.FAN_TOTAL_DURATION = system_state.FAN_MAX_RUNTIME = 0
    system_state.INTERNAL_HIGH_TEMP = system_state.INTERNAL_LOW_TEMP = system_state.INTERNAL_TEMP
    system_state.INTERNAL_HIGH_HUMIDITY = system_state.INTERNAL_LOW_HUMIDITY = system_state.INTERNAL_HUMIDITY
    system_state.EXTERNAL_HIGH_TEMP = system_state.EXTERNAL_LOW_TEMP = system_state.EXTERNAL_TEMP
    system_state.EXTERNAL_HIGH_HUMIDITY = system_state.EXTERNAL_LOW_HUMIDITY = system_state.EXTERNAL_HUMIDITY
    system_state.AMBIENT_HIGH_TEMP = system_state.AMBIENT_LOW_TEMP = system_state.AMBIENT_TEMP
    system_state.AMBIENT_HIGH_HUMIDITY = system_state.AMBIENT_LOW_HUMIDITY = system_state.AMBIENT_HUMIDITY

def cleanup():
    # Want to add code here to update display, update log with run time etc
    global running
    stop_event.set()
    print('Cleaning Up')
    running = False
    sensor_thread.join()  # Wait for the sensor thread to finish
    notifier.stop_worker()
    try:
        display_manager.switch_image(Screen.SHUTDOWN)
        display_manager.display_current_image(BONNETDisplay.disp)
        # make sure fan is off
        fanController.set_fan_speed(0)
        time.sleep(3)
        BONNETDisplay.clear_screen()
    except NameError:
        print('LCD Not Defined')
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'FATAL',
                   'System', 'System', "No display available...")
    finally:
        logger.log(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO',
                   'System', 'System', "System Shutting down..")

def save_config():
    configManager.save_config()
    logger.log( time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO', 'SYSTEM', 'CONFIG',
                "Config File Updated")

def isDeviceDetected(statuses, device):
    for status in statuses:
        if device in status and 'Detected' in status:
            return True
    return False

if __name__ == "__main__":

    i2c = SafeI2C()
    system_stats = None

    # Register signal handlers at program startup
    signal.signal(signal.SIGINT, handle_shutdown)  # kill -2
    signal.signal(signal.SIGTERM, handle_shutdown)  # kill -15

    # BEGIN STATUS CHECKS ETC
    # First check for the installed devices.
    installed_devices = read_installed_devices(configManager)
    overall_status, statuses = systemstatus.query_i2c_devices(installed_devices)
    print(f"Overall status: {overall_status}")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    for status in statuses:
        print(status)
        logger.log(timestamp, 'INFO', 'SYSTEM', 'STATUS', status)

    if overall_status == 'bad':
        logger.log(timestamp, 'WARN', 'SYSTEM', 'OVERALL', "Overall Status: Fail")
        print("Overall Status: Fail")
        # raise ValueError("Overall Status Failed")
    # The below logs the HW stats as well as the log file information
    log_system_status()
    # END STATUS CHECKS

    logger.log( time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'INFO', 'SYSTEM', 'SYSTEM',
                "System Starting Up...")

    # Variables to manage button state and humidity values
    last_press_time = {'up': 0, 'dn': 0}
    last_page_changed = time.time()

    # Global state variables
    current_frame_index = 0

    # GPIO setup using gpiozero for input buttons
    btn_lt = Button(system_state.BTN_L_PIN, pull_up=True, bounce_time=0.1, hold_time=system_state.BUTTON_HOLD_TIME)
    btn_rt = Button(system_state.BTN_R_PIN, pull_up=True, bounce_time=0.1, hold_time=system_state.BUTTON_HOLD_TIME)
    btn_up = Button(system_state.BTN_U_PIN, pull_up=True, bounce_time=0.1, hold_time=system_state.BUTTON_HOLD_TIME)
    btn_dn = Button(system_state.BTN_D_PIN, pull_up=True, bounce_time=0.1, hold_time=system_state.BUTTON_HOLD_TIME)
    btn_ctr = Button(system_state.BTN_C_PIN, pull_up=True, bounce_time=0.1, hold_time=system_state.BUTTON_HOLD_TIME)
    btn_a = Button(system_state.BTN_A_PIN, pull_up=True, bounce_time=0.1, hold_time=system_state.BUTTON_HOLD_TIME)
    btn_b = Button(system_state.BTN_B_PIN, pull_up=True, bounce_time=0.1, hold_time=system_state.BUTTON_HOLD_TIME)

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
    stop_event = threading.Event()
    sensor_thread = threading.Thread(target=sensor, args=(stop_event,))

    try:
        # Initialize displays...
        # Need to do this first so if there is an error cleanup can still work...
        print('Initializing Primary Display...')
        BONNET_display_config = DisplayConfig(font_path=system_state.FONT, font_size=system_state.FONTSIZE, border_size=system_state.BORDER)
        BONNETDisplay = BONNETDisplay(BONNET_display_config)
        display_manager = OLEDDisplayManager(BONNET_display_config,240,240, font=BONNETDisplay.font)

        display_manager.switch_image(Screen.INITIAL)
        display_manager.display_current_image(BONNETDisplay.disp)
        time.sleep(2)

        # Initialize the stats screens
        update_stats()

        # Initialize to show the first page
        show_page(system_state.current_page)

        # Initialize fan controller
        print('Initializing fan controller...')
        fanController = EMC2101Controller(i2c_board=i2c)
        time.sleep(2)

        # Initialise the internal sensor
        internalsensor = Sensor('SHT4X_Internal', 0x44)

        # Initialize the external sensor
        if isDeviceDetected(statuses, 'SHTC3'):
            externalsensor = Sensor('SHTC3', 0x70)
        else:
            externalsensor = Sensor('SHT4X_External', 0x44)

        # Initialise the ambient sensor
        ambientsensor = Sensor('SHT4X_Ambient', 0x44)

        # Initialize previous output values to None
        internalprevious_output = {'temperature': 0, 'humidity': 0}
        INTERNAL_PREVIOUS_HUMIDITY = 0
        externalprevious_output = {'temperature': 0, 'humidity': 0}
        EXTERNAL_PREVIOUS_HUMIDITY = 0
        ambientprevious_output = {'temperature': 0, 'humidity': 0}
        AMBIENT_PREVIOUS_HUMIDITY = 0

        # This should happen when things are reset
        if system_state.INITIAL_STARTUP == "True":
            ambientoutput = ambientsensor.read_sensor()
            AMBIENT_TEMP = AMBIENT_LOW_TEMP = AMBIENT_HIGH_TEMP = ambientoutput['temperature'] = celsius_to_fahrenheit(ambientoutput['temperature'])
            ambientprevious_output = ambientoutput
            AMBIENT_PREVIOUS_HUMIDITY = AMBIENT_HUMIDITY = AMBIENT_LOW_HUMIDITY = AMBIENT_HIGH_HUMIDITY = ambientoutput['humidity']
            internaloutput = internalsensor.read_sensor()
            INTERNAL_TEMP = INTERNAL_LOW_TEMP = INTERNAL_HIGH_TEMP = internaloutput['temperature'] = celsius_to_fahrenheit(internaloutput['temperature'])
            internalprevious_output = internaloutput
            INTERNAL_PREVIOUS_HUMIDITY = INTERNAL_HUMIDITY = INTERNAL_LOW_HUMIDITY = INTERNAL_HIGH_HUMIDITY = internaloutput['humidity']
            externaloutput = externalsensor.read_sensor()
            EXTERNAL_TEMP = EXTERNAL_LOW_TEMP = EXTERNAL_HIGH_TEMP = externaloutput['temperature'] = celsius_to_fahrenheit(externaloutput['temperature'])
            externalprevious_output = externaloutput
            EXTERNAL_PREVIOUS_HUMIDITY = EXTERNAL_HUMIDITY = EXTERNAL_LOW_HUMIDITY = EXTERNAL_HIGH_HUMIDITY = externaloutput['humidity']
            save_config()

        schedule_tasks(int_interval=system_state.TASK_INTERNAL, fan_interval=system_state.TASK_FAN)

        # Send the startup status now?
        send_status(message="Startup status")
        # Start the threading.

        sensor_thread.start()
        # time.sleep(2)
        run_scheduler()

        # TODO:
        ## These should be placed where they need to be
        # # Recondition internal sensor using external as reference
        # internalsensor.recondition_sensor(ref_sensor=externalsensor)
        #
        # # Recondition external sensor by itself
        # externalsensor.recondition_sensor()

    except KeyboardInterrupt as e:
        print("\nValue Error!", e)
    except ValueError as e:
        print("\nValue Error!",e)
    except OSError as e:
        print("\nOS Error!", e)
    except NameError as e:
        print("\nName Error!",e)
    finally:
        cleanup()
