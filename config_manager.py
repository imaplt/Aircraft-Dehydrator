import configparser

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
    
    def get_config(self, section, key):
        return self.config.get(section, key)

    def get_int_config(self, section, key):
        return self.config.getint(section, key)
    
    def display_config(self):
        for section in self.config.sections():
            print(f"[{section}]")
            for key in self.config[section]:
                print(f"{key} = {self.config[section][key]}")
        if 'DEFAULT' in self.config:
            print("[DEFAULT]")
            for key in self.config['DEFAULT']:
                print(f"{key} = {self.config['DEFAULT'][key]}")
    
    def update_config(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)