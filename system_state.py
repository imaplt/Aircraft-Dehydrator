class SystemState:
    def __init__(self):
        # Config values (loaded from config.ini at startup)
        self.min_temp = 40
        self.max_temp = 70
        self.min_humidity = 20
        self.max_humidity = 60
        self.fan_cycle_time = 30  # seconds

        # Runtime state (changes while running)
        self.current_temp = 0.0
        self.current_humidity = 0.0
        self.fan_running = False