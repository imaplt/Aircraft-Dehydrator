import configparser
from datetime import timedelta


class ConfigManager:
    def __init__(self, filename, system_state):
        self.config_file = filename
        self.parser = configparser.ConfigParser()
        self.system_state = system_state

    def load_config(self):
        self.parser.read(self.config_file)

        self.system_state.INITIAL_STARTUP = self.get_config('DEFAULT',"initial_startup", fallback=self.system_state.INITIAL_STARTUP)
        self.system_state.LOGFILE = self.get_config('DEFAULT',"logfile", fallback=self.system_state.LOGFILE)
        self.system_state.MAX_LOG_SIZE = self.get_int_config('DEFAULT',"max_log_size", fallback=self.system_state.MAX_LOG_SIZE)
        self.system_state.MAX_ARCHIVE_SIZE = self.get_int_config('DEFAULT',"max_archive_size", fallback=self.system_state.MAX_ARCHIVE_SIZE)
        self.system_state.FONT = self.get_config('DEFAULT',"font", fallback=self.system_state.FONT)
        self.system_state.FONTSIZE = self.get_int_config('DEFAULT',"fontsize", fallback=self.system_state.FONTSIZE)
        self.system_state.BORDER = self.get_int_config('DEFAULT',"border", fallback=self.system_state.BORDER)

        # Initialise the logging and pull numbers from the config.
        self.system_state.INTERNAL_HIGH_TEMP = self.get_float_config('LOG', 'internal_high_temp')
        self.system_state.INTERNAL_LOW_TEMP = self.get_float_config('LOG', 'internal_low_temp')
        self.system_state.INTERNAL_HIGH_HUMIDITY = self.get_float_config('LOG', 'internal_high_humidity')
        self.system_state.INTERNAL_LOW_HUMIDITY = self.get_float_config('LOG', 'internal_low_humidity')
        self.system_state.EXTERNAL_HIGH_TEMP = self.get_float_config('LOG', 'external_high_temp')
        self.system_state.EXTERNAL_LOW_TEMP = self.get_float_config('LOG', 'external_low_temp')
        self.system_state.EXTERNAL_HIGH_HUMIDITY = self.get_float_config('LOG', 'external_high_humidity')
        self.system_state.EXTERNAL_LOW_HUMIDITY = self.get_float_config('LOG', 'external_low_humidity')
        self.system_state.AMBIENT_HIGH_TEMP = self.get_float_config('LOG', 'ambient_high_temp')
        self.system_state.AMBIENT_LOW_TEMP = self.get_float_config('LOG', 'ambient_low_temp')
        self.system_state.AMBIENT_HIGH_HUMIDITY = self.get_float_config('LOG', 'ambient_high_humidity')
        self.system_state.AMBIENT_LOW_HUMIDITY = self.get_float_config('LOG', 'ambient_low_humidity')
        self.system_state.MIN_HUMIDITY = self.get_float_config('LOG', 'min_humidity')
        self.system_state.MAX_HUMIDITY = self.get_float_config('LOG', 'max_humidity')
        self.system_state.CYCLE_COUNT = self.get_int_config('LOG','cycle_count', fallback=self.system_state.CYCLE_COUNT)
        self.system_state.FAN_TOTAL_DURATION = self.get_duration_config('LOG', 'FAN_TOTAL_DURATION')
        self.system_state.FAN_MAX_RUNTIME = self.get_duration_config('LOG', 'FAN_MAX_RUNTIME')
        self.system_state.FAN_LIMIT = self.get_duration_config('DEFAULT', 'FAN_LIMIT')
        self.system_state.FAN_LIMIT_TIMEOUT = self.get_duration_config('DEFAULT', 'FAN_LIMIT_TIMEOUT')

        # … and so on for the rest …

    def save_config(self):
        # General
        self.update_config("initial_startup", self.system_state.INITIAL_STARTUP)
        self.update_config("logfile", self.system_state.LOGFILE)
        self.update_config("max_log_size", self.system_state.MAX_LOG_SIZE)
        self.update_config("max_archive_size", self.system_state.MAX_ARCHIVE_SIZE)

        # Display
        self.update_config("font", self.system_state.FONT)
        self.update_config("fontsize", self.system_state.FONTSIZE)
        self.update_config("border", self.system_state.BORDER)

        # Internal
        self.update_config("internal_high_temp", self.system_state.INTERNAL_HIGH_TEMP, "LOG")
        self.update_config("internal_low_temp", self.system_state.INTERNAL_LOW_TEMP, "LOG")
        self.update_config("internal_high_humidity", self.system_state.INTERNAL_HIGH_HUMIDITY, "LOG")
        self.update_config("internal_low_humidity", self.system_state.INTERNAL_LOW_HUMIDITY, "LOG")

        # External
        self.update_config("external_high_temp", self.system_state.EXTERNAL_HIGH_TEMP, "LOG")
        self.update_config("external_low_temp", self.system_state.EXTERNAL_LOW_TEMP, "LOG")
        self.update_config("external_high_humidity", self.system_state.EXTERNAL_HIGH_HUMIDITY, "LOG")
        self.update_config("external_low_humidity", self.system_state.EXTERNAL_LOW_HUMIDITY, "LOG")

        # Ambient
        self.update_config("ambient_high_temp", self.system_state.AMBIENT_HIGH_TEMP, "LOG")
        self.update_config("ambient_low_temp", self.system_state.AMBIENT_LOW_TEMP, "LOG")
        self.update_config("ambient_high_humidity", self.system_state.AMBIENT_HIGH_HUMIDITY, "LOG")
        self.update_config("ambient_low_humidity", self.system_state.AMBIENT_LOW_HUMIDITY, "LOG")

        # Cycle / fan
        self.update_config("cycle_count", self.system_state.CYCLE_COUNT, "LOG")
        self.set_duration_config("fan_total_duration", self.system_state.FAN_TOTAL_DURATION, "LOG")
        self.set_duration_config("fan_max_runtime", self.system_state.FAN_MAX_RUNTIME, "LOG")
        self.set_duration_config("fan_limit", self.system_state.FAN_LIMIT, "DEFAULT")
        self.set_duration_config("fan_limit_timeout", self.system_state.FAN_LIMIT_TIMEOUT, "DEFAULT")

        # Misc
        self.update_config("UOM", self.system_state.UOM)

        # Write file
        with open(self.config_file, "w") as configfile:
            self.parser.write(configfile)

    # --------------------------
    # Helpers with fallbacks
    # --------------------------
    def get_config(self, section, key, fallback=None):
        return self.parser.get(section, key, fallback=fallback)

    def get_int_config(self, section, key, fallback=None):
        return self.parser.getint(section, key, fallback=fallback)

    def get_float_config(self, section, key, fallback=None):
        return self.parser.getfloat(section, key, fallback=fallback)

    def get_boolean_config(self, section, key, fallback=None):
        return self.parser.getboolean(section, key, fallback=fallback)

    def get_duration_config(self, section, key, fallback=None):
        seconds = self.parser.getfloat(section, key, fallback=fallback.total_seconds() if fallback else 0)
        return timedelta(seconds=seconds)

    def set_duration_config(self, key, value, section="LOG"):
        if section != "DEFAULT" and not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, key, str(int(value.total_seconds())))

    def update_config(self, key, value, section="CUSTOM"):
        if section != "DEFAULT" and not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, key, str(value))

