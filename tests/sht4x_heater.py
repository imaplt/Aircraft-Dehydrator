import time
import board
import busio
import adafruit_sht4x
import adafruit_shtc3

# Setup I2C bus and sensors
i2c = busio.I2C(board.SCL, board.SDA)
sht40 = adafruit_sht4x.SHT4x(i2c)
# Set precision to high and no heat
sht40.mode = 0xFD
shtc3 = adafruit_shtc3.SHTC3(i2c)

print("Found SHT40 with serial:", sht40.serial_number)
print("Current mode is: ", adafruit_sht4x.Mode.string[sht40.mode])
print("Found SHTC3")

# Helper function
def read_sensors(label="Reading"):
    # SHT40 normal mode
    t40, rh40 = sht40.measurements
    # SHTC3 (returns a namedtuple with temperature, relative_humidity)
    t3, rh3 = shtc3.measurements
    print(
        f"{label} | "
        f"SHT40: {t40:.2f} °C, {rh40:.2f} %RH   ||   "
        f"SHTC3: {t3:.2f} °C, {rh3:.2f} %RH"
    )

# 1. Baseline
read_sensors("Baseline")

# 2. Heater test on SHT40
print("\nStarting SHT40 1s heater cycle (60 iterations)...")
for i in range(60):
    # Use SHT40 1s heater mode
    sht40.mode =  0x39
    t40, rh40 = sht40.measurements

    # Normal reading from SHTC3
    t3, rh3 = shtc3.measurements

    print(
        f"Heater cycle {i+1:02d} | "
        f"SHT40: {t40:.2f} °C, {rh40:.2f} %RH   ||   "
        f"SHTC3: {t3:.2f} °C, {rh3:.2f} %RH"
    )
    time.sleep(2)

# 3. Heater off, immediate reading
sht40.mode = 0xFD
print("\nHeater OFF reading:")
read_sensors("Post-heater")

# 4. Pause 60 seconds

print("\nPausing for 90s...")
time.sleep(90)

# 5. Final stabilized reading
print("\nFinal reading after 90 sec rest:")
read_sensors("Final")
