import time

import adafruit_shtc3
import board
import adafruit_sht4x
import adafruit_tca9548a
import adafruit_sht31d
import adafruit_bitbangio
from enum import Enum
from safei2c import SafeI2C

# Define constants
# Sensor Ports on Multiplexer
# Mux address
MUX_ADDR = 0x70  # Default address for TCA9548A multiplexer
INTERNAL_SENSOR_PORT = 0
EXTERNAL_SENSOR_PORT = 1
AMBIENT_SENSOR_PORT = 7

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

# Create a dictionary mapping hex values to string descriptions
hex_to_description = {
    SHT4X_NOHEAT_HIGHPRECISION: "High precision measurement, no heater",
    SHT4X_NOHEAT_MEDPRECISION: "Medium precision measurement, no heater",
    SHT4X_NOHEAT_LOWPRECISION: "Low precision measurement, no heater",
    SHT4X_HIGHHEAT_1S: "High precision measurement, high heat for 1 sec",
    SHT4X_HIGHHEAT_100MS: "High precision measurement, high heat for 0.1 sec",
    SHT4X_MEDHEAT_1S: "High precision measurement, med heat for 1 sec",
    SHT4X_MEDHEAT_100MS: "High precision measurement, med heat for 0.1 sec",
    SHT4X_LOWHEAT_1S: "High precision measurement, low heat for 1 sec",
    SHT4X_LOWHEAT_100MS: "High precision measurement, low heat for 0.1 sec",
    SHT4X_READSERIAL: "Read Out of Serial Register",
    SHT4X_SOFTRESET: "Soft Reset"
}

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

# Shared singletons
_I2C = None
_MUX = None
_BITBANG_I2C = None

class Sensor:

    def __init__(self, sensor_type, address):
        global _I2C, _MUX, _BITBANG_I2C

        self.sensor_type = sensor_type
        self.address = address

        # Ensure one shared I2C object
        if _I2C is None:
            # _I2C = busio.I2C(board.SCL, board.SDA)
            _I2C = SafeI2C()

        # Ensure one mux object
        if _MUX is None:
            _MUX = adafruit_tca9548a.TCA9548A(_I2C, address=MUX_ADDR)

        # Lazy-init for bitbang bus since it's slower and specific pins
        if sensor_type == "SHT30" and _BITBANG_I2C is None:
            _BITBANG_I2C = adafruit_bitbangio.I2C(board.D27, board.D22)

        # Attach correct sensor type
        if sensor_type == "SHT4X_Internal":
            self.sensor = adafruit_sht4x.SHT4x(_MUX[INTERNAL_SENSOR_PORT])

        elif sensor_type == "SHT4X_External":
            self.sensor = adafruit_sht4x.SHT4x(_MUX[EXTERNAL_SENSOR_PORT])

        elif sensor_type == "SHT4X_Ambient":
            self.sensor = adafruit_sht4x.SHT4x(_MUX[AMBIENT_SENSOR_PORT])

        elif sensor_type == "SHTC3":
            self.sensor = adafruit_shtc3.SHTC3(_I2C)

        elif sensor_type == "SHT30":
            self.sensor = adafruit_sht31d.SHT31D(_BITBANG_I2C, address)

        else:
            raise ValueError(
                "Invalid sensor type. Supported types: 'SHT4X_Internal', "
                "'SHT4X_External', 'SHT4X_Ambient', 'SHTC3', 'SHT30'"
            )

    def sensor_status(self):
        if self.sensor_type == 'SHT30':
            status = self.sensor.status
        else:
            raise ValueError("Invalid sensor type. Supported types: 'SHT30'")
        return status

    def sensor_mode(self):
        mode = self.sensor.mode
        return hex_to_description.get(mode, "Unknown mode")

    def read_sensor(self):

        if self.sensor_type[:5] == 'SHT4X':
            temperature, humidity = self.sensor.measurements
        elif self.sensor_type == 'SHT30':
            temperature = self.sensor.temperature
            humidity = self.sensor.relative_humidity
        elif self.sensor_type == 'SHTC3':
            self.sensor.low_power = False
            temperature = self.sensor.temperature
            humidity = self.sensor.relative_humidity
        else:
            raise ValueError("Invalid sensor type. Supported types: 'SHT4X', 'SHTC3', 'SHT30'")

        # Format the sensor output to one decimal place
        temperature = round(temperature, 1)
        humidity = round(humidity, 1)

        return {'temperature': temperature, 'humidity': humidity}

    def heat_sensor(self, duration=5):
        # Run high-heat on SHT4X sensors.
        if not isinstance(self.sensor, adafruit_sht4x.SHT4x):
            print(f"{self.sensor_type} does not support heating.")
            return
        try:
            print(f"Heating {self.sensor_type} on HIGH for {duration}s...")
            self.sensor.mode = adafruit_sht4x.SHT4X_MEDHEAT_1S
            time.sleep(duration)
            # return to normal mode
            self.sensor.mode = adafruit_sht4x.SHT4X_NOHEAT_HIGHPRECISION
        except Exception as e:
            print(f"Heat cycle error: {e}")

    def cooldown_sensors(self, ref_sensor=None, threshold_f=1.5, max_wait=60):
        """
        Wait until sensor cools down.
        - If ref_sensor is provided: wait until |temp - ref_temp| <= threshold
        - If not: wait until temp is close to baseline.
        """
        start_time = time.time()
        baseline_temp, _ = (self.read_sensor() if ref_sensor is None else (None, None))

        while True:
            temp, _ = self.read_sensor()
            if temp is None:
                break

            if ref_sensor:
                ref_temp, _ = ref_sensor.read_sensor()
                if ref_temp is None:
                    break
                if abs((temp * 9 / 5 + 32) - (ref_temp * 9 / 5 + 32)) <= threshold_f:
                    print("Cooldown reached (relative to ref sensor).")
                    break
            else:
                if baseline_temp is not None:
                    if abs((temp * 9 / 5 + 32) - (baseline_temp * 9 / 5 + 32)) <= threshold_f:
                        print("Cooldown reached (baseline).")
                        break

            if (time.time() - start_time) > max_wait:
                print("Cooldown timeout reached.")
                break

            time.sleep(1)

    def recondition_sensor(self, ref_sensor=None, heat_duration=5, threshold_f=1.5, max_wait=60):
        """
        Recondition this sensor: run heat cycle + wait for cooldown.
        Optionally compare cooldown against a reference sensor.
        """
        self.heat_sensor(duration=heat_duration)
        self.cooldown_sensors(ref_sensor=ref_sensor, threshold_f=threshold_f, max_wait=max_wait)