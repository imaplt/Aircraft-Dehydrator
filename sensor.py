import time
import board
import busio
import adafruit_sht4x
import adafruit_sht31d
import adafruit_bitbangio
from enum import Enum

# Define constants
SHT4X_NOHEAT_HIGHPRECISION = 0xFD  # High precision measurement, no heater
SHT4X_NOHEAT_MEDPRECISION = 0xF6  # Medium precision measurement, no heater
SHT4X_NOHEAT_LOWPRECISION = 0xE0  # Low precision measurement, no heater

SHT4X_HIGHHEAT_1S = 0x39  # High precision measurement, high heat for 1 sec
SHT4X_HIGHHEAT_100MS = 0x32  # High precision measurement, high heat for 0.1 sec
SHT4X_MEDHEAT_1S = 0x2F  # High precision measurement, med heat for 1 sec
SHT4X_MEDHEAT_100MS = 0x24  # High precision measurement, med heat for 0.1 sec
SHT4X_LOWHEAT_1S = 0x1E  # High precision measurement, low heat for 1 sec
SHT4X_LOWHEAT_100MS = 0x15  # High precision measurement, low heat for 0.1 sec

SHT4X_READSERIAL = 0x89  # Read Out of Serial Register
SHT4X_SOFTRESET = 0x94  # Soft Reset


# Define enums
class SHT4XPrecision(Enum):
    HIGH_PRECISION = "High Precision"
    MED_PRECISION = "Medium Precision"
    LOW_PRECISION = "Low Precision"


class SHT4XHeater(Enum):
    NO_HEATER = "No Heater"
    HIGH_HEATER_1S = "High Heater 1s"
    HIGH_HEATER_100MS = "High Heater 100ms"
    MED_HEATER_1S = "Med Heater 1s"
    MED_HEATER_100MS = "Med Heater 100ms"
    LOW_HEATER_1S = "Low Heater 1s"
    LOW_HEATER_100MS = "Low Heater 100ms"

# # Example usage
# print(f"High precision no heater code: {SHT4X_NOHEAT_HIGHPRECISION}")
# print(f"Soft reset code: {SHT4X_SOFTRESET}")
#
# # Using enums
# precision = SHT4XPrecision.HIGH_PRECISION
# heater_setting = SHT4XHeater.HIGH_HEATER_1S
#
# print(f"Selected precision: {precision}")
# print(f"Selected heater setting: {heater_setting}")

class Sensor:
    def __init__(self, sensor_type, address):
        self.sensor_type = sensor_type
        self.address = address

        if sensor_type == 'SHT41':
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_sht4x.SHT4x(self.i2c, address)

        elif sensor_type == 'SHT30':
            self.i2c = adafruit_bitbangio.I2C(board.D27, board.D22)
            self.sensor = adafruit_sht31d.SHT31D(self.i2c, address)
        else:
            raise ValueError("Invalid sensor type. Supported types: 'SHT41', 'SHT30'")

    def sensor_status(self):

        if self.sensor_type == 'SHT30':
            status = self.sensor.status
        else:
            raise ValueError("Invalid sensor type. Supported types: 'SHT30'")
        return status

    def sensor_mode(self):
        mode = self.sensor.mode
        return mode

    def read_sensor(self):

        if self.sensor_type == 'SHT41':
            temperature, humidity = self.sensor.measurements
        elif self.sensor_type == 'SHT30':
            temperature = self.sensor.temperature
            humidity = self.sensor.relative_humidity
        else:
            raise ValueError("Invalid sensor type. Supported types: 'SHT41', 'SHT30'")

        # Format the sensor output to one decimal place
        temperature = round(temperature, 1)
        humidity = round(humidity, 1)

        return {'temperature': temperature, 'humidity': humidity}

    def heat_sensor(self):
        if self.sensor_type == 'SHT41':
            self.sensor.heater = True
            time.sleep(1)
            self.sensor.heater = False
        elif self.sensor_type == 'SHT30':
            self.sensor.heater = True
            time.sleep(1)
            self.sensor.heater = False
        else:
            raise ValueError("Invalid sensor type. Supported types: 'SHT41', 'SHT30'")
