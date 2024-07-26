import configparser


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
        else:
            raise KeyError(f"Config for DEFAULT/{key} not found.")
    
    def display_config(self):
        for section in self.config.sections():
            print(f"[{section}]")
            for key in self.config[section]:
                print(f"{key} = {self.config[section][key]}")
        if 'DEFAULT' in self.config:
            print("[DEFAULT]")
            for key in self.config['DEFAULT']:
                print(f"{key} = {self.config['DEFAULT'][key]}")
    
    def update_config(self, key, value):
        if not self.config.has_section("CUSTOM"):
            self.config.add_section("CUSTOM")
        self.config.set("CUSTOM", key, value)
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
