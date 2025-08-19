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
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

# Create the TCA9548A object and give it the I2C bus
tca = adafruit_tca9548a.TCA9548A(i2c)

# For each sensor, create it using the TCA9548A channel instead of the I2C object
sht4X_internal = adafruit_sht4x.SHT4x(tca[0])
sht4X_external = adafruit_sht4x.SHT4x(tca[1])
sht41 = adafruit_sht4x.SHT4x(tca[7])


# Internal sensor
print(
    f"Detected, temperature: {sht4X_internal.temperature:.2f} C, humidity: {sht4X_internal.relative_humidity:.2f} %")

# External sensor
print(
    f"Detected, temperature: {sht4X_external.temperature:.2f} C, humidity: {sht4X_external.relative_humidity:.2f} %")

print(
    f"Detected, temperature: {sht41.temperature:.2f} C, humidity: {sht41.relative_humidity:.2f} %")

