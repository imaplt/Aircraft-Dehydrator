# main.py

import time
import board
import busio
from display import SSD1308Display
from sensor import Sensor

def main():
    # Initialize I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # Create an instance of the SSD1308Display class
    display = SSD1308Display(128, 64, i2c)

    # Display centered text
    display.display_centered_text("Hello, World!")
    time.sleep(1)

    sht30_sensor = Sensor('SHT30', 0x44)
    sht41_sensor = Sensor('SHT41', 0x44)
    start_time = time.time()
    print(start_time)


    while True:
        current_time = time.time()
        # Read and print sensor data every 2 seconds
        if int(current_time - start_time) % 2 == 0:
            sht41_output = sht41_sensor.read_sensor()
            sht30_output = sht30_sensor.read_sensor()
            print("SHT41 Sensor Reading:", sht41_output)
            print("SHT30 Sensor Reading:", sht30_output)
            display.display_centered_text(f"SHT41 - {sht41_output['temperature']}°C")
        
        # Heat the sensors every 30 seconds
        if int(current_time - start_time) % 30 == 0:
            print("Heating SHT41 sensor...")
            sht41_sensor.heat_sensor()
            print("Heating SHT30 sensor...")
            sht30_sensor.heat_sensor()
        
        # Sleep for a short duration to avoid multiple reads/heats within the same second
        time.sleep(0.1)

if __name__ == "__main__":
    main()
