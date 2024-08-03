import schedule
import time
from config_manager import ConfigManager
from logger import Logger as Log
import system_status
from display import SSD1306Display, DisplayConfig


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

    # Initialise the logging
    logger = Log(LOGFILE, MAX_LOG_SIZE, MAX_ARCHIVE_SIZE)

    try:
        installed_devices = read_installed_devices(configManager)
        overall_status, statuses = system_status.query_i2c_devices(installed_devices)
        print(f"Overall status: {overall_status}")

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for status in statuses:
            print(status)
            logger.log(timestamp, 'System', '', status)
        if overall_status == 'Bad':
            logger.log(timestamp, 'System', 'Overall', "Overall Status: Fail")
            raise ValueError("Overall Status Failed")

        schedule_tasks()
        # run_scheduler()

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
