import board
import adafruit_emc2101
import time
from adafruit_bus_device.i2c_device import I2CDevice


class EMC2101:
    def __init__(self, i2c_address=0x4C):
        self.i2c = board.I2C()
        self.sensor = adafruit_emc2101.EMC2101(self.i2c)
        self.fan_engaged = False
        self.fan_engaged_time = 0
        self.start_time = time.time()
        self.fan_engage_start_time = None
        self.I2C_ADDRESS = 0x4C
        self.INTERNAL_TEMP_REG = 0x00
        self.EXTERNAL_TEMP_REG = 0x01
        self.FAN_SPEED_REG = 0x10
        self.FAN_SPEED_SET_REG = 0x11
        self.STATUS_REG = 0x02
        self.CONFIG_REG = 0x03
        self.RESET_REG = 0x05
        self.device = I2CDevice(self.i2c, self.I2C_ADDRESS)

    def _read_register(self, register):
        with self.device:
            self.device.write(bytes([register]))
            result = bytearray(1)
            self.device.readinto(result)
        return result[0]

    def read_config(self):
        config = self._read_register(self.CONFIG_REG)
        config_description = []

        if config & 0x01:
            config_description.append("Device enabled")
        else:
            config_description.append("Device disabled")
        if config & 0x02:
            config_description.append("Fan control enabled")
        else:
            config_description.append("Fan control disabled")
        if config & 0x04:
            config_description.append("Temperature monitoring enabled")
        else:
            config_description.append("Temperature monitoring disabled")

        return ", ".join(config_description)

    def read_internal_temp(self):
        temp = self.sensor.internal_temperature
        return temp

    def read_external_temp(self):
        temp = self.sensor.external_temperature
        return temp

    def read_fan_speed(self):
        fan_speed = self.sensor.fan_speed
        return fan_speed

    def set_fan_speed(self, speed):
        if 0 <= speed <= 100:
            # Disengage code
            if speed == 0:
                # Disengaged fan code
                if self.fan_engaged:
                    # Put code here to stop the fan.
                    self.fan_engaged = False
                    self.sensor.manual_fan_speed = speed
                    time.sleep(1)
                    last_run_time = time.time() - self.start_time
                    return True, last_run_time
                else:
                    return False, None
            # Engage code (speed greater than 0)
            else:
                if not self.fan_engaged:
                    # Put code here to start fan...
                    self.sensor.manual_fan_speed = speed
                    time.sleep(1)
                    self.fan_engaged = True
                    return True
                else:
                    return False
        else:
            raise ValueError("Fan speed must be between 0 and 100")

    def read_status(self):
        status = self.sensor.devstatus
        status_description = []
        if status & 0x01:
            status_description.append("Internal temperature sensor fault")
        if status & 0x02:
            status_description.append("External temperature sensor fault")
        if status & 0x04:
            status_description.append("Fan speed fault")
        if status & 0x08:
            status_description.append("Device reset")

        if not status_description:
            status_description.append("No faults")
        return ", ".join(status_description)
