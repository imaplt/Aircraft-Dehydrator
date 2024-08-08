import configparser
from datetime import timedelta


class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_config(self, key):
        if "CUSTOM" in self.config and key in self.config["CUSTOM"]:
            return self.config["CUSTOM"][key]
        elif "DEFAULT" in self.config and key in self.config["DEFAULT"]:
            return self.config["DEFAULT"][key]
        else:
            raise KeyError(f"Config for DEFAULT/{key} not found.")

    def get_int_config(self, key):
        if "CUSTOM" in self.config and key in self.config["CUSTOM"]:
            return int(self.config["CUSTOM"][key])
        elif "DEFAULT" in self.config and key in self.config["DEFAULT"]:
            return int(self.config["DEFAULT"][key])
        elif "LOG" in self.config and key in self.config["LOG"]:
            return int(self.config["LOG"][key])
        else:
            raise KeyError(f"Config for {key} not found.")

    def get_float_config(self, section, key):
        return float(self.config[section][key])

    def get_boolean_config(self, key, section='DEFAULT'):
        return self.config.getboolean(section, key)

    def get_duration_config(self, section, key):
        # Retrieve the total cycle duration in seconds
        total_cycle_duration_seconds = int(self.config.getfloat(section, key))
        # Convert the total seconds back to a timedelta object
        return timedelta(seconds=total_cycle_duration_seconds)

    def set_duration_config(self, key, value, section='LOG'):
        self.config.set(section, key, str(value.total_seconds()))
        self.save_config()

    def display_config(self):
        for section in self.config.sections():
            print(f"[{section}]")
            for key in self.config[section]:
                print(f"{key} = {self.config[section][key]}")
        if 'DEFAULT' in self.config:
            print("[DEFAULT]")
            for key in self.config['DEFAULT']:
                print(f"{key} = {self.config['DEFAULT'][key]}")
    
    def update_config(self, key, value, section='CUSTOM'):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
