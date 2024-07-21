import time
import board
import busio
import adafruit_sht4x
import adafruit_sht31d
import adafruit_bitbangio

class Sensor:
    def __init__(self, sensor_type, address):
        self.sensor_type = sensor_type
        self.address = address
        
        if sensor_type == 'SHT41':
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = adafruit_sht4x.SHT4x(self.i2c, address)
        elif sensor_type == 'SHT30':
           self.i2c = adafruit_bitbangio.I2C(board.D27,board.D22)
           self.sensor = adafruit_sht31d.SHT31D(self.i2c, address)
        else:
            raise ValueError("Invalid sensor type. Supported types: 'SHT41', 'SHT30'")

    def read_sensor(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

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

        return {'timestamp': timestamp, 'temperature': temperature, 'humidity': humidity}

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
