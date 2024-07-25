import time


class HumidityController:
    def __init__(self):
        self.fan_engaged = False
        self.fan_engaged_time = 0
        self.start_time = time.time()
        self.fan_engage_start_time = None

    @staticmethod
    def engage_fan(self):
        if not self.fan_engaged:
            # Put code here to start fan...
            self.fan_engaged = True
            return True
        else:
            return False

    @staticmethod
    def disengage_fan(self):
        if self.fan_engaged:
            # Put code here to stop the fan.
            self.fan_engaged = False
            last_run_time = time.time() - self.start_time
            return True, last_run_time
        else:
            return False, None

    def fan_status(self):
        # Placeholder for actual fan status and RPM retrieval logic
        status = "on" if self.fan_engaged else "off"
        rpm = 1200 if self.fan_engaged else 0  # Example RPM values
        last_run_time = time.time() - self.start_time
        return status, rpm, last_run_time
