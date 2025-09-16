import board
import busio
import adafruit_sht31d
import adafruit_tca9548a
import adafruit_sht4x
import adafruit_shtc3
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import adafruit_ssd1306
import adafruit_bitbangio
import digitalio
from fan_controller import EMC2101Controller
from adafruit_rgb_display import st7789
from safei2c import SafeI2C


# Constants
I2C_SCL = board.SCL
I2C_SDA = board.SDA
MUX_SCL = board.SCL
MUX_SDA = board.SDA
EXTERNAL_SCL = board.D27
EXTERNAL_SDA = board.D22

# Mux address
MUX_ADDR = 0x70  # Default address for TCA9548A multiplexer

# Sensor Ports on Multiplexer
INTERNAL_SENSOR_PORT = 0
EXTERNAL_SENSOR_PORT = 1
AMBIENT_SENSOR_PORT = 7

# SHT4X Constants
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


def _celsius_to_fahrenheit(celsius):
    fahrenheit = (celsius * 9 / 5) + 32
    return round(fahrenheit, 1)

def _format_status(temp, humidity):
    """Return formatted status string for temperature + humidity."""
    return "Detected, temperature: {:.1f} F, humidity: {:.1f} %".format(_celsius_to_fahrenheit(temp), humidity)

class SystemStatus:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.i2c = SafeI2C()  # always use the safe wrapper
        return cls._instance

    def detect_mux_and_sht4X(self, devices, overall_status_var=None):
        try:
            mux = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDR)
            devices["MUX"]["status"] = "Detected"

            # Internal sensor
            if INTERNAL_SENSOR_PORT < len(mux):
                sht4X_internal = adafruit_sht4x.SHT4x(mux[INTERNAL_SENSOR_PORT])
                devices["SHT4X_Internal"]["status"] = (
                    f"Detected, temperature: {_celsius_to_fahrenheit(sht4X_internal.temperature):.1f} F, humidity: "
                    f"{sht4X_internal.relative_humidity:.1f} %")
                print(f"Detected, temperature: {_celsius_to_fahrenheit(sht4X_internal.temperature):.1f} F, humidity: "
                      f"{sht4X_internal.relative_humidity:.1f} %")
            # External sensor
            if EXTERNAL_SENSOR_PORT < len(mux):
                sht4X_external = adafruit_sht4x.SHT4x(mux[EXTERNAL_SENSOR_PORT])
                devices["SHT4X_External"]["status"] = (
                    f"Detected, temperature: {_celsius_to_fahrenheit(sht4X_external.temperature):.1f} F, humidity: "
                    f"{sht4X_external.relative_humidity:.1f} %"
                )
                print(f"Detected, temperature: {_celsius_to_fahrenheit(sht4X_external.temperature):.1f} F, humidity: "
                      f"{sht4X_external.relative_humidity:.1f} %")
                # External sensor
            if AMBIENT_SENSOR_PORT < len(mux):
                sht4X_ambient = adafruit_sht4x.SHT4x(mux[AMBIENT_SENSOR_PORT])
                devices["SHT4X_Ambient"]["status"] = (
                    f"Detected, temperature: {_celsius_to_fahrenheit(sht4X_ambient.temperature):.1f} F, humidity: "
                    f"{sht4X_ambient.relative_humidity:.1f} %"
                )
                print(
                    f"Detected, temperature: {_celsius_to_fahrenheit(sht4X_ambient.temperature):.1f} F, humidity: "
                    f"{sht4X_ambient.relative_humidity:.1f} %")

        except Exception as e:
            devices["MUX"]["status"] = f"Error: {str(e)}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_sht30(self, devices, overall_status_var=None):
        try:
            i2c = adafruit_bitbangio.I2C(board.D27, board.D22)
            sensor = adafruit_sht31d.SHT31D(i2c, 0x44)
            devices["SHT30"]["status"] = (
                "Detected, temperature: {:.2f} F, humidity: {:.2f} %"
            ).format(_celsius_to_fahrenheit(sensor.temperature), sensor.relative_humidity)
        except OSError as e:
            devices["SHT30"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"
        except Exception as e:
            devices["SHT30"]["status"] = f"Unexpected error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_shtc3(self, devices, overall_status_var=None):
        try:
            # i2c = busio.I2C(board.SCL, board.SDA)
            shtc3 = adafruit_shtc3.SHTC3(self.i2c)
            devices["SHTC3"]["status"] = (
                "Detected, temperature: {:.1f} F, humidity: {:.1f} %"
            ).format(_celsius_to_fahrenheit(shtc3.temperature), shtc3.relative_humidity)
        except OSError as e:
            devices["SHTC3"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"
        except Exception as e:
            devices["SHTC3"]["status"] = f"Unexpected error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_sht4X_internal(self, devices, overall_status_var=None):
        try:
            mux = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDR)
            sht4X = adafruit_sht4x.SHT4x(mux[INTERNAL_SENSOR_PORT])
            print("Found SHT4x with serial number", hex(sht4X.serial_number))
            sht4X.mode = SHT4X_NOHEAT_HIGHPRECISION
            print("Current mode is: ", adafruit_sht4x.Mode.string[sht4X.mode])
            devices["SHT4X_Internal"]["status"] = (
                "Detected, temperature: {:.1f} F, humidity: {:.1f} %"
            ).format(  _celsius_to_fahrenheit(sht4X.temperature), sht4X.relative_humidity)

        except OSError as e:
            devices["SHT4X_Internal"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"
        except Exception as e:
            devices["SHT4X_Internal"]["status"] = f"Unexpected error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_sht4X_external(self, devices, overall_status_var=None):
        try:

            mux = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDR)
            sht4X = adafruit_sht4x.SHT4x(mux[EXTERNAL_SENSOR_PORT])
            devices["SHT4X_External"]["status"] = (
                "Detected, temperature: {:.1f} F, humidity: {:.1f} %"
            ).format(_celsius_to_fahrenheit(sht4X.temperature), sht4X.relative_humidity)
        except OSError as e:
            devices["SHT4X_External"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"
        except Exception as e:
            devices["SHT4X_External"]["status"] = f"Unexpected error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_sht4X_ambient(self, devices, overall_status_var=None):
        try:

            mux = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDR)
            sht4X = adafruit_sht4x.SHT4x(mux[AMBIENT_SENSOR_PORT])
            devices["SHT4X_Ambient"]["status"] = (
                "Detected, temperature: {:.1f} F, humidity: {:.1f} %"
            ).format(_celsius_to_fahrenheit(sht4X.temperature), sht4X.relative_humidity)
        except OSError as e:
            devices["SHT4X_Ambient"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"
        except Exception as e:
            devices["SHT4X_Ambient"]["status"] = f"Unexpected error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_lcd2004(self, devices, overall_status_var=None):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            lcd = character_lcd.Character_LCD_I2C(i2c, 20, 4, devices["LCD2004"]["address"])
            devices["LCD2004"]["status"] = "Detected"
        except Exception as e:
            devices["LCD2004"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_lcd1602(self, devices, overall_status_var=None):
        try:
            lcd = character_lcd.Character_LCD_I2C(self.i2c, 16, 2, devices["LCD1602"]["address"])
            devices["LCD1602"]["status"] = "Detected"
        except Exception as e:
            devices["LCD1602"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_emc2101(self, devices, overall_status_var=None):
        try:
            emc2101 = EMC2101Controller(self.i2c)
            status = emc2101.read_status()
            devices["EMC2101"]["status"] = f"Detected, Status: {status}"
        except Exception as e:
            devices["EMC2101"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_fan(self, devices, overall_status_var=None):
        try:
            fan = EMC2101Controller(self.i2c)
            if fan.read_fan_speed() > 200:
                devices["FAN"]["status"] = f"Currently Running, RPM: {fan.read_fan_speed()}"
            else:
                fan.set_fan_speed(100)
                rpm = fan.read_fan_speed()
                temp = fan.read_internal_temp()
                fan.set_fan_speed(0)
                if rpm >= 3000:
                    devices["FAN"]["status"] = f"Detected, RPM: {rpm}, Internal Temp: {temp}"
                else:
                    devices["FAN"]["status"] = f"Not Detected, RPM: {rpm}; Should be > 3200"
                    if overall_status_var is not None:
                        overall_status_var["status"] = "bad"
        except Exception as e:
            devices["FAN"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_ssd1306(self, devices, overall_status_var=None):
        try:
            oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c)
            devices["SSD1306"]["status"] = "Detected"
        except Exception as e:
            devices["SSD1306"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def detect_bonnet(self, devices, overall_status_var=None):
        try:
            BAUDRATE = 24000000
            HEIGHT = 240
            Y_OFFSET = 80
            ROTATION = 180

            spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
            cs_pin = digitalio.DigitalInOut(board.CE0)
            dc_pin = digitalio.DigitalInOut(board.D25)
            reset_pin = digitalio.DigitalInOut(board.D24)

            disp = st7789.ST7789(
                spi,
                height=HEIGHT,
                y_offset=Y_OFFSET,
                rotation=ROTATION,
                cs=cs_pin,
                dc=dc_pin,
                rst=reset_pin,
                baudrate=BAUDRATE
            )
            devices["BONNET"]["status"] = "Detected"
        except OSError as e:
            devices["BONNET"]["status"] = f"Error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"
        except Exception as e:
            devices["BONNET"]["status"] = f"Unexpected error: {e}"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"

    def query_i2c_devices(self, installed_devices):
        devices = {
            "SHT30": {"address": 0x44, "status": "Not detected"},
            "SHTC3": {"address": 0x70, "status": "Not detected"},
            "SHT4X_Internal": {"address": 0x44, "status": "Not detected"},
            "SHT4X_External": {"address": 0x44, "status": "Not detected"},
            "SHT4X_Ambient": {"address": 0x44, "status": "Not detected"},
            "LCD2004": {"address": 0x27, "status": "Not detected"},
            "LCD1602": {"address": 0x27, "status": "Not detected"},
            "BONNET": {"address": 0x00, "status": "Not detected"},
            "EMC2101": {"address": 0x4C, "status": "Not detected"},
            "FAN": {"address": 0x3C, "status": "Not detected"},
            "SSD1306": {"address": 0x3C, "status": "Not detected"},
            "MUX": {"address": 0x70, "status": "Not detected"}
        }
        overall_status_var = {"status": "good"}

        detection_map = {
            "SHT30": self.detect_sht30,
            "SHTC3": self.detect_shtc3,
            "SHT4X_Internal": self.detect_sht4X_internal,
            "SHT4X_External": self.detect_sht4X_external,
            "SHT4X_Ambient": self.detect_sht4X_external,
            "LCD2004": self.detect_lcd2004,
            "LCD1602": self.detect_lcd1602,
            "EMC2101": self.detect_emc2101,
            "FAN": self.detect_fan,
            "SSD1306": self.detect_ssd1306,
            "BONNET": self.detect_bonnet,
            "MUX": self.detect_mux_and_sht4X
        }

        for device in installed_devices:
            if device in detection_map:
                detection_map[device](devices, overall_status_var)

        statuses = [f"{dev}: {devices[dev]['status']}" for dev in installed_devices]
        return overall_status_var["status"], statuses
