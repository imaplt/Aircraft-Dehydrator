import time
from fan_controller import EMC2101


class HumidityController:
    def __init__(self):
        self.fan_engaged = False
        self.fan_engaged_time = 0
        self.start_time = time.time()
        self.fan_engage_start_time = None
        self.emc2101 = EMC2101()

    def engage_fan(self):
        if not self.fan_engaged:
            # Put code here to start fan...
            self.emc2101.set_fan_speed(25)
            self.fan_engaged = True
            return True
        else:
            return False

    def disengage_fan(self):
        if self.fan_engaged:
            # Put code here to stop the fan.
            self.fan_engaged = False
            self.emc2101.set_fan_speed(0)
            last_run_time = time.time() - self.start_time
            return True, last_run_time
        else:
            return False, None

    def fan_status(self):
        # Placeholder for actual fan status and RPM retrieval logic
        # status = "on" if self.fan_engaged else "off"
        status = self.emc2101.read_status()
        config = self.emc2101.read_config()
        rpm = self.emc2101.read_fan_speed()
        temp = self.emc2101.read_internal_temp()
        print("Device Status:", status)
        print("Device Configuration:", config)
        print("RPM:", rpm)
        print("Temperature:", temp)
        print("Fan Engaged:", self.fan_engaged)
        # rpm = 1200 if self.fan_engaged else 0  # Example RPM values
        last_run_time = time.time() - self.start_time
        return status, config, rpm, last_run_time
