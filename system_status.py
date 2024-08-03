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
            devices["EMC2101"]["status"] = f"Detected, Status: {status}"
        except Exception as e:
            devices["EMC2101"]["status"] = f"Error: {str(e)}"
            overall_status = "bad"

    if "FAN" in installed_devices:
        try:
            fan = EMC2101()
            fan.set_fan_speed(100)
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
            devices["FAN"]["status"] = f"Error: {str(e)}"
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
