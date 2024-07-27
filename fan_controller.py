import board
import adafruit_emc2101


class EMC2101:
    def __init__(self, i2c_address=0x4C):
        self.i2c = board.I2C()
        self.sensor = adafruit_emc2101.EMC2101(self.i2c)

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
            self.sensor.manual_fan_speed = speed
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

    def read_config(self):
        config = self.sensor.devconfig
        return config
