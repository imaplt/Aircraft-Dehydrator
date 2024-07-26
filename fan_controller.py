import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice


class EMC2101:
    # Define the I2C address and relevant registers based on the datasheet
    I2C_ADDRESS = 0x4C
    INTERNAL_TEMP_REG = 0x00
    EXTERNAL_TEMP_REG = 0x01
    FAN_SPEED_REG = 0x10
    FAN_SPEED_SET_REG = 0x11
    STATUS_REG = 0x02
    CONFIG_REG = 0x03
    RESET_REG = 0x05

    def __init__(self, bus=1):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.device = I2CDevice(self.i2c, self.I2C_ADDRESS)

    def read_register(self, register):
        with self.device:
            self.device.write(bytes([register]))
            result = bytearray(1)
            self.device.readinto(result)
        return result[0]

    def write_register(self, register, value):
        with self.device:
            self.device.write(bytes([register, value]))

    def read_internal_temp(self):
        temp = self.read_register(self.INTERNAL_TEMP_REG)
        return temp

    def read_external_temp(self):
        temp = self.read_register(self.EXTERNAL_TEMP_REG)
        return temp

    def read_fan_speed(self):
        fan_speed = self.read_register(self.FAN_SPEED_REG)
        return fan_speed

    def set_fan_speed(self, speed):
        if 0 <= speed <= 255:
            self.write_register(self.FAN_SPEED_SET_REG, speed)
        else:
            raise ValueError("Fan speed must be between 0 and 255")

    def read_status(self):
        status = self.read_register(self.STATUS_REG)
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

    def reset_device(self):
        self.write_register(self.RESET_REG, 0xFF)

    def read_config(self):
        config = self.read_register(self.CONFIG_REG)
        return config

    # print("Internal Temperature:", emc2101.read_internal_temp(), "°C")
    # print("External Temperature:", emc2101.read_external_temp(), "°C")
    #
    # print("Current Fan Speed:", emc2101.read_fan_speed())
    #
    # new_fan_speed = 128
    # emc2101.set_fan_speed(new_fan_speed)
    # print(f"Set Fan Speed to: {new_fan_speed}")
    # print("New Fan Speed:", emc2101.read_fan_speed())
    #
    # print("Device Status:", emc2101.read_status())
    # print("Device Configuration:", emc2101.read_config())
    #
    # # Reset the device
    # emc2101.reset_device()
    # print("Device reset performed.")
