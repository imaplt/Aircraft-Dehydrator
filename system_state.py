class SystemState:
    def __init__(self):
        # defaults (same as before)
        self.INITIAL_STARTUP = "True"
        self.LOGFILE = "log.csv"
        self.MAX_LOG_SIZE = 5242880
        self.MAX_ARCHIVE_SIZE = 5242880000
        self.FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        self.FONTSIZE = 24
        self.BORDER = 5
        self.INTERNAL_HIGH_TEMP = 0
        self.INTERNAL_LOW_TEMP = 0
        self.INTERNAL_HIGH_HUMIDITY = 0
        self.INTERNAL_LOW_HUMIDITY = 0
        self.EXTERNAL_HIGH_TEMP = 0
        self.EXTERNAL_LOW_TEMP = 0
        self.EXTERNAL_HIGH_HUMIDITY = 0
        self.EXTERNAL_LOW_HUMIDITY = 0
        self.AMBIENT_HIGH_TEMP = 0
        self.AMBIENT_LOW_TEMP = 0
        self.AMBIENT_HIGH_HUMIDITY = 0
        self.AMBIENT_LOW_HUMIDITY = 0
        self.CYCLE_COUNT = 0
        self.FAN_TOTAL_DURATION = 0.0
        self.FAN_MAX_RUNTIME = 0.0
        self.FAN_LIMIT = 120
        self.FAN_LIMIT_TIMEOUT = 60
        self.fan_limit_exceeded_count = 0
        self.MAX_EXCEEDED_ATTEMPTS = 3
        self.UOM = "F"

        self.runtime = 0
        self.FAN_RUNNING = True
        self.FAN_RUNNING_TIME = 0
        self.FAN_DURATION = 0.0
        self.INTERNAL_PREVIOUS_HUMIDITY = 0
        self.EXTERNAL_PREVIOUS_HUMIDITY = 0
        self.AMBIENT_PREVIOUS_HUMIDITY = 0
        self.EXTERNAL_TEMP = 0
        self.INTERNAL_TEMP = 0
        self.AMBIENT_TEMP = 0
        self.EXTERNAL_HUMIDITY = 0
        self.INTERNAL_HUMIDITY = 0
        self.AMBIENT_HUMIDITY = 0
        self.MIN_HUMIDITY = 0.0
        self.MAX_HUMIDITY = 0.0

        self.humidity_mode = "selection"
        self.humidity_changed = False
        self.humidity_selected = "max"
        self.humidity_blink_state = True
        self.mode = None
        self.max_color = "white"
        self.min_color = "white"

        self.selected_option = 1

        self.current_page = 0
        self.page_changed = False
        self.page_index = 0
        self.last_press_time = 0
        self.total_pages = 7

        # Set task intervals
        self.TASK_FAN = 15
        self.TASK_INTERNAL = 1
        self.TASK_EXTERNAL = 1

        # Get button pin info
        self.BTN_L_PIN = 27
        self.BTN_R_PIN = 23
        self.BTN_U_PIN = 17
        self.BTN_D_PIN = 22
        self.BTN_C_PIN = 4
        self.BTN_A_PIN = 5
        self.BTN_B_PIN = 6
        self.BUTTON_HOLD_TIME = 3

        self.shutdown_timer = None


    def update_from_config(self, parser):
        self.INITIAL_STARTUP = parser.get_config("initial_startup")
        self.LOGFILE = parser.get_config("logfile")
        self.MAX_LOG_SIZE = parser.get_int_config("max_log_size")
        self.MAX_ARCHIVE_SIZE = parser.get_int_config("max_archive_size")
        self.FONT = parser.get_config("font")
        self.FONTSIZE = parser.get_int_config("fontsize")
        self.BORDER = parser.get_int_config("border")

        self.INTERNAL_HIGH_TEMP = parser.get_float_config("LOG", "internal_high_temp")
        self.INTERNAL_LOW_TEMP = parser.get_float_config("LOG", "internal_low_temp")
        self.INTERNAL_HIGH_HUMIDITY = parser.get_float_config("LOG", "internal_high_humidity")
        self.INTERNAL_LOW_HUMIDITY = parser.get_float_config("LOG", "internal_low_humidity")
        self.EXTERNAL_HIGH_TEMP = parser.get_float_config("LOG", "external_high_temp")
        self.EXTERNAL_LOW_TEMP = parser.get_float_config("LOG", "external_low_temp")
        self.EXTERNAL_HIGH_HUMIDITY = parser.get_float_config("LOG", "external_high_humidity")
        self.EXTERNAL_LOW_HUMIDITY = parser.get_float_config("LOG", "external_low_humidity")
        self.AMBIENT_HIGH_TEMP = parser.get_float_config("LOG", "ambient_high_temp")
        self.AMBIENT_LOW_TEMP = parser.get_float_config("LOG", "ambient_low_temp")
        self.AMBIENT_HIGH_HUMIDITY = parser.get_float_config("LOG", "ambient_high_humidity")
        self.AMBIENT_LOW_HUMIDITY = parser.get_float_config("LOG", "ambient_low_humidity")

        self.CYCLE_COUNT = parser.get_int_config("cycle_count")
        self.FAN_TOTAL_DURATION = parser.get_duration_config("LOG", "FAN_TOTAL_DURATION")
        self.FAN_MAX_RUNTIME = parser.get_duration_config("LOG", "FAN_MAX_RUNTIME")
        self.FAN_LIMIT = parser.get_duration_config("DEFAULT", "FAN_LIMIT")
        self.FAN_LIMIT_TIMEOUT = parser.get_duration_config("DEFAULT", "FAN_LIMIT_TIMEOUT")

        self.fan_limit_exceeded_count = 0
        self.MAX_EXCEEDED_ATTEMPTS = 3
        self.UOM = parser.get_config("UOM")
        self.MIN_HUMIDITY = parser.get_int_config('min_humidity')
        self.MAX_HUMIDITY = parser.get_int_config('max_humidity')
        self.FAN_DURATION = parser.get_int_config('fan_duration')
        # Set task intervals
        self.TASK_FAN = parser.get_int_config('TASK_FAN')
        self.TASK_INTERNAL = parser.get_int_config('TASK_INTERNAL')
        self.TASK_EXTERNAL = parser.get_int_config('TASK_EXTERNAL')

        # Get button pin info
        self.BTN_L_PIN = parser.get_int_config('BTN_L_PIN')
        self.BTN_R_PIN = parser.get_int_config('BTN_R_PIN')
        self.BTN_U_PIN = parser.get_int_config('BTN_U_PIN')
        self.BTN_D_PIN = parser.get_int_config('BTN_D_PIN')
        self.BTN_C_PIN = parser.get_int_config('BTN_C_PIN')
        self.BTN_A_PIN = parser.get_int_config('BTN_A_PIN')
        self.BTN_B_PIN = parser.get_int_config('BTN_B_PIN')

    def save_to_config(self, parser):
        parser.set_config("initial_startup", self.INITIAL_STARTUP)
        parser.set_config("logfile", self.LOGFILE)
        parser.set_int_config("max_log_size", self.MAX_LOG_SIZE)
        parser.set_int_config("max_archive_size", self.MAX_ARCHIVE_SIZE)
        parser.set_config("font", self.FONT)
        parser.set_int_config("fontsize", self.FONTSIZE)
        parser.set_int_config("border", self.BORDER)

        parser.set_float_config("LOG", "internal_high_temp", self.INTERNAL_HIGH_TEMP)
        parser.set_float_config("LOG", "internal_low_temp", self.INTERNAL_LOW_TEMP)
        parser.set_float_config("LOG", "internal_high_humidity", self.INTERNAL_HIGH_HUMIDITY)
        parser.set_float_config("LOG", "internal_low_humidity", self.INTERNAL_LOW_HUMIDITY)
        parser.set_float_config("LOG", "external_high_temp", self.EXTERNAL_HIGH_TEMP)
        parser.set_float_config("LOG", "external_low_temp", self.EXTERNAL_LOW_TEMP)
        parser.set_float_config("LOG", "external_high_humidity", self.EXTERNAL_HIGH_HUMIDITY)
        parser.set_float_config("LOG", "external_low_humidity", self.EXTERNAL_LOW_HUMIDITY)
        parser.set_float_config("LOG", "ambient_high_temp", self.AMBIENT_HIGH_TEMP)
        parser.set_float_config("LOG", "ambient_low_temp", self.AMBIENT_LOW_TEMP)
        parser.set_float_config("LOG", "ambient_high_humidity", self.AMBIENT_HIGH_HUMIDITY)
        parser.set_float_config("LOG", "ambient_low_humidity", self.AMBIENT_LOW_HUMIDITY)

        parser.set_int_config("cycle_count", self.CYCLE_COUNT)
        parser.set_duration_config("LOG", "FAN_TOTAL_DURATION", self.FAN_TOTAL_DURATION)
        parser.set_duration_config("LOG", "FAN_MAX_RUNTIME", self.FAN_MAX_RUNTIME)
        parser.set_duration_config("DEFAULT", "FAN_LIMIT", self.FAN_LIMIT)
        parser.set_duration_config("DEFAULT", "FAN_LIMIT_TIMEOUT", self.FAN_LIMIT_TIMEOUT)

        parser.set_config("UOM", self.UOM)
