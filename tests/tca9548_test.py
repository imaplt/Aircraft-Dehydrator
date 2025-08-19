# SPDX-FileCopyrightText: 2021 Carter Nelson for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example shows using TCA9548A to perform a simple scan for connected devices
import board
import adafruit_tca9548a
import adafruit_sht4x
import qwiic_tca9548a
import qwiic_i2c
import time
import sys

# Create I2C bus as normal
# i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
# Get the I2C driver
i2c = qwiic_i2c.getI2CDriver()

# Create the TCA9548A object and give it the I2C bus
tca = adafruit_tca9548a.TCA9548A(i2c)

for channel in range(8):
    if tca[channel].try_lock():
        print(f"Channel {channel}:", end="")
        addresses = tca[channel].scan()
        print([hex(address) for address in addresses if address != 0x70])
        tca[channel].unlock()



print("\nSparkFun TCA9548A 8-Channel Mux Example\n")

# Create an instance of the Qwiic TCA9548A object
myTca = qwiic_tca9548a.QwiicTCA9548A()
mux = adafruit_tca9548a.TCA9548A(i2c)

# Check if the device is connected
if not myTca.connected:
    print("The Qwiic TCA9548A 8-Channel Mux device isn't connected to the system. Please check your connection",
          file=sys.stderr)



print("\n--- Enabling Channels 0 and 1 ---")
myTca.disable_all()  # Disable all channels first
myTca.enable_channels([0, 1, 7]) # Enable specific channels
myTca.list_channels() # List current channel status

print("Checking for I2C devices on ports 0, 1 and 7:")
devices = i2c.scan()
print("Devices found:", devices)

# Internal sensor
sht4X_internal = adafruit_sht4x.SHT4x(mux[0])
print(
    f"Detected, temperature: {sht4X_internal.temperature:.2f} C, humidity: {sht4X_internal.relative_humidity:.2f} %")

# External sensor
sht4X_external = adafruit_sht4x.SHT4x(myTca[1])
print(
    f"Detected, temperature: {sht4X_external.temperature:.2f} C, humidity: {sht4X_external.relative_humidity:.2f} %")


