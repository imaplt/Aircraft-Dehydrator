import time

import board
import busio
import adafruit_sht31d
import adafruit_sht4x
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import adafruit_ssd1306
from adafruit_bus_device.i2c_device import I2CDevice
import adafruit_bitbangio
from fan_controller import EMC2101


class SystemStatus:
    I2C_ADDRESS = 0x4C
    INTERNAL_TEMP_REG = 0x00
    EXTERNAL_TEMP_REG = 0x01
    FAN_SPEED_REG = 0x10
    FAN_SPEED_SET_REG = 0x11
    STATUS_REG = 0x02
    CONFIG_REG = 0x03
    RESET_REG = 0x05

    def __init__(self, i2c):
        self.device = I2CDevice(i2c, self.I2C_ADDRESS)

    def read_register(self, register):
        with self.device:
            self.device.write(bytes([register]))
            result = bytearray(1)
            self.device.readinto(result)
        return result[0]

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

    def read_config(self):
        config = self.read_register(self.CONFIG_REG)
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


def query_i2c_devices(installed_devices):
    i2c = busio.I2C(board.SCL, board.SDA)

    devices = {
        "SHT30": {"address": 0x44, "status": "Not detected"},
        "SHT41_Internal": {"address": 0x44, "status": "Not detected"},
        "SHT41_External": {"address": 0x44, "status": "Not detected"},
        "LCD2004": {"address": 0x27, "status": "Not detected"},
        "LCD1602": {"address": 0x27, "status": "Not detected"},
        "EMC2101": {"address": 0x4C, "status": "Not detected"},
        "FAN": {"address": 0x3C, "status": "Not detected"},
        "SSD1306": {"address": 0x3C, "status": "Not detected"}
    }
    overall_status = "good"
    statuses = []

    if "SHT30" in installed_devices:
        try:
            # The SHT30 uses a non-standard I2C interface
            i2c = adafruit_bitbangio.I2C(board.D27, board.D22)
            sensor = adafruit_sht31d.SHT31D(i2c, 0x44)
            devices["SHT30"]["status"] = ("Detected, temperature: {:.2f} C,"
                                          " humidity: {:.2f} %").format(sensor.temperature, sensor.relative_humidity)
        except Exception as e:
            devices["SHT30"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    if "SHT41_Internal" in installed_devices:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            sht41 = adafruit_sht4x.SHT4x(i2c)
            devices["SHT41_Internal"]["status"] = ("Detected, temperature: {:.2f} C,"
                                          " humidity: {:.2f} %").format(sht41.temperature, sht41.relative_humidity)
        except Exception as e:
            devices["SHT41_Internal"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    if "SHT41_External" in installed_devices:
        try:
            i2c = busio.I2C(board.D27, board.D22)
            sht41 = adafruit_sht4x.SHT4x(i2c)
            devices["SHT41_External"]["status"] = ("Detected, temperature: {:.2f} C,"
                                          " humidity: {:.2f} %").format(sht41.temperature, sht41.relative_humidity)
        except Exception as e:
            devices["SHT41_External"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    if "LCD2004" in installed_devices:
        try:
            lcd2004 = character_lcd.Character_LCD_I2C(i2c, 20, 4, devices["LCD2004"]["address"])
            devices["LCD2004"]["status"] = "Detected"
        except Exception as e:
            devices["LCD2004"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    if "LCD1602" in installed_devices:
        try:
            lcd1602 = character_lcd.Character_LCD_I2C(i2c, 16, 2, devices["LCD1602"]["address"])
            devices["LCD1602"]["status"] = "Detected"
        except Exception as e:
            devices["LCD1602"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    if "EMC2101" in installed_devices:
        try:
            emc2101 = EMC2101()
            status = emc2101.read_status()
            # config = emc2101.read_config()
            devices["EMC2101"]["status"] = f"Detected, Status: {status}"
        except Exception as e:
            devices["EMC2101"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    if "FAN" in installed_devices:
        try:
            fan = EMC2101()
            fan.set_fan_speed(100)
            time.sleep(1)
            rpm = fan.read_fan_speed()
            temp = fan.read_internal_temp()
            fan.set_fan_speed(0)
            if rpm >= 4000:
                devices["FAN"]["status"] = f"Detected, RPM: {rpm}, Internal Temp: {temp}"
                overall_status = "good"
            else:
                devices["FAN"]["status"] = f"Not Detected, RPM: {rpm}; Should be > 4000"
                overall_status = "bad"
        except Exception as e:
            devices["EMC2101"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    if "SSD1306" in installed_devices:
        try:
            oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
            devices["SSD1306"]["status"] = "Detected"
        except Exception as e:
            devices["SSD1306"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    for device in installed_devices:
        statuses.append(f"{device}: {devices[device]['status']}")

    return overall_status, statuses
