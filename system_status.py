import board
import busio
import adafruit_sht31d
import adafruit_sht4x
import adafruit_shtc3
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import adafruit_ssd1306
import adafruit_bitbangio
import digitalio
from fan_controller import EMC2101
from adafruit_rgb_display import st7789

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


# Helper: Safe cleanup
def safe_deinit(*resources):
    """Safely deinitialize hardware resources without throwing errors."""
    for res in resources:
        if hasattr(res, "deinit"):
            try:
                res.deinit()
            except Exception:
                pass


# Individual device detection functions
def detect_sht30(devices, overall_status_var=None):
    i2c = sensor = None
    try:
        i2c = adafruit_bitbangio.I2C(board.D27, board.D22)
        sensor = adafruit_sht31d.SHT31D(i2c, 0x44)
        devices["SHT30"]["status"] = (
            "Detected, temperature: {:.2f} C, humidity: {:.2f} %"
        ).format(sensor.temperature, sensor.relative_humidity)
    except OSError as e:
        devices["SHT30"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    except Exception as e:
        devices["SHT30"]["status"] = f"Unexpected error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    finally:
        safe_deinit(sensor, i2c)


def detect_shtc3(devices, overall_status_var=None):
    i2c = shtc3 = None
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        shtc3 = adafruit_shtc3.SHTC3(i2c)
        devices["SHTC3"]["status"] = (
            "Detected, temperature: {:.2f} C, humidity: {:.2f} %"
        ).format(shtc3.temperature, shtc3.relative_humidity)
    except OSError as e:
        devices["SHTC3"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    except Exception as e:
        devices["SHTC3"]["status"] = f"Unexpected error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    finally:
        safe_deinit(shtc3, i2c)


def detect_sht41_internal(devices, overall_status_var=None):
    i2c = sht41 = None
    try:
        i2c = board.I2C()  # uses board.SCL and board.SDA
        # i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
        sht41 = adafruit_sht4x.SHT4x(i2c)
        print("Found SHT4x with serial number", hex(sht41.serial_number))

        # sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
        # Can also set the mode to enable heater
        # sht41.mode = adafruit_sht4x.Mode.LOWHEAT_100MS

        sht41.mode = 0x39
        print("Current mode is: ", adafruit_sht4x.Mode.string[sht41.mode])
        devices["SHT41_Internal"]["status"] = (
            "Detected, temperature: {:.2f} C, humidity: {:.2f} %"
        ).format(sht41.temperature, sht41.relative_humidity)
        sht41.mode = 0xFD
        print("Current mode is: ", adafruit_sht4x.Mode.string[sht41.mode])

    except OSError as e:
        devices["SHT41_Internal"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    except Exception as e:
        devices["SHT41_Internal"]["status"] = f"Unexpected error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    finally:
        safe_deinit(sht41, i2c)


def detect_sht41_external(devices, overall_status_var=None):
    i2c = sht41 = None
    try:
        i2c = busio.I2C(board.D27, board.D22)
        sht41 = adafruit_sht4x.SHT4x(i2c)
        devices["SHT41_External"]["status"] = (
            "Detected, temperature: {:.2f} C, humidity: {:.2f} %"
        ).format(sht41.temperature, sht41.relative_humidity)
    except OSError as e:
        devices["SHT41_External"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    except Exception as e:
        devices["SHT41_External"]["status"] = f"Unexpected error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    finally:
        safe_deinit(sht41, i2c)


def detect_lcd2004(devices, overall_status_var=None):
    i2c = lcd = None
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        lcd = character_lcd.Character_LCD_I2C(i2c, 20, 4, devices["LCD2004"]["address"])
        devices["LCD2004"]["status"] = "Detected"
    except Exception as e:
        devices["LCD2004"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    finally:
        safe_deinit(lcd, i2c)


def detect_lcd1602(devices, overall_status_var=None):
    i2c = lcd = None
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        lcd = character_lcd.Character_LCD_I2C(i2c, 16, 2, devices["LCD1602"]["address"])
        devices["LCD1602"]["status"] = "Detected"
    except Exception as e:
        devices["LCD1602"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    finally:
        safe_deinit(lcd, i2c)


def detect_emc2101(devices, overall_status_var=None):
    try:
        emc2101 = EMC2101()
        status = emc2101.read_status()
        devices["EMC2101"]["status"] = f"Detected, Status: {status}"
    except Exception as e:
        devices["EMC2101"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"


def detect_fan(devices, overall_status_var=None):
    try:
        fan = EMC2101()
        fan.set_fan_speed(100)
        rpm = fan.read_fan_speed()
        temp = fan.read_internal_temp()
        fan.set_fan_speed(0)
        if rpm >= 3400:
            devices["FAN"]["status"] = f"Detected, RPM: {rpm}, Internal Temp: {temp}"
        else:
            devices["FAN"]["status"] = f"Not Detected, RPM: {rpm}; Should be > 4000"
            if overall_status_var is not None:
                overall_status_var["status"] = "bad"
    except Exception as e:
        devices["FAN"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"


def detect_ssd1306(devices, overall_status_var=None):
    i2c = oled = None
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
        devices["SSD1306"]["status"] = "Detected"
    except Exception as e:
        devices["SSD1306"]["status"] = f"Error: {e}"
        if overall_status_var is not None:
            overall_status_var["status"] = "bad"
    finally:
        safe_deinit(oled, i2c)


def detect_bonnet(devices, overall_status_var=None):
    spi = cs_pin = dc_pin = reset_pin = disp = None
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
    finally:
        safe_deinit(disp, spi, cs_pin, dc_pin, reset_pin)


# Main function: runs all checks in list
def query_i2c_devices(installed_devices):
    devices = {
        "SHT30": {"address": 0x44, "status": "Not detected"},
        "SHTC3": {"address": 0x70, "status": "Not detected"},
        "SHT41_Internal": {"address": 0x44, "status": "Not detected"},
        "SHT41_External": {"address": 0x44, "status": "Not detected"},
        "LCD2004": {"address": 0x27, "status": "Not detected"},
        "LCD1602": {"address": 0x27, "status": "Not detected"},
        "BONNET": {"address": 0x00, "status": "Not detected"},
        "EMC2101": {"address": 0x4C, "status": "Not detected"},
        "FAN": {"address": 0x3C, "status": "Not detected"},
        "SSD1306": {"address": 0x3C, "status": "Not detected"}
    }
    overall_status_var = {"status": "good"}

    detection_map = {
        "SHT30": detect_sht30,
        "SHTC3": detect_shtc3,
        "SHT41_Internal": detect_sht41_internal,
        "SHT41_External": detect_sht41_external,
        "LCD2004": detect_lcd2004,
        "LCD1602": detect_lcd1602,
        "EMC2101": detect_emc2101,
        "FAN": detect_fan,
        "SSD1306": detect_ssd1306,
        "BONNET": detect_bonnet
    }

    for device in installed_devices:
        if device in detection_map:
            detection_map[device](devices, overall_status_var)

    statuses = [f"{dev}: {devices[dev]['status']}" for dev in installed_devices]
    return overall_status_var["status"], statuses
