import time


def read_sensor(sensor):
    """
    Safely read temperature (°C) and relative humidity (%) from a sensor.
    Returns (temperature_c, humidity) or (None, None) if error.
    """
    try:
        return sensor.temperature, sensor.relative_humidity
    except Exception as e:
        print(f"Sensor read error: {e}")
        return None, None


def heat_sensor(sensor, duration=5):
    """
    Run high heat on the sensor for the given duration (seconds).
    """
    try:
        print(f"Heating sensor {sensor} on HIGH for {duration}s...")
        sensor.mode = sensor.TEMP_AND_HUMIDITY_HIGH_HEATER_1S
        time.sleep(duration)
        # return to normal mode
        sensor.mode = sensor.TEMP_AND_HUMIDITY
    except Exception as e:
        print(f"Heat cycle error: {e}")


def cooldown_sensors(sensor_a, sensor_b=None, threshold_f=1.5, max_wait=60):
    """
    Wait until sensors cool down enough.
    - If sensor_b is provided: wait until |temp_a - temp_b| <= threshold_f
    - If only sensor_a: wait until it cools to within threshold_f of its baseline
    """
    start_time = time.time()
    baseline_temp = None
    if sensor_b is None:
        baseline_temp, _ = read_sensor(sensor_a)

    while True:
        temp_a, _ = read_sensor(sensor_a)
        if temp_a is None:
            break

        if sensor_b:
            temp_b, _ = read_sensor(sensor_b)
            if temp_b is None:
                break
            if abs((temp_a * 9 / 5 + 32) - (temp_b * 9 / 5 + 32)) <= threshold_f:
                print("Cooldown reached (sensors within threshold).")
                break
        else:
            if baseline_temp is not None:
                if abs((temp_a * 9 / 5 + 32) - (baseline_temp * 9 / 5 + 32)) <= threshold_f:
                    print("Cooldown reached (single sensor baseline).")
                    break

        if (time.time() - start_time) > max_wait:
            print("Cooldown timeout reached.")
            break

        time.sleep(1)


def recondition_sensor(sensor, sensor_ref=None, heat_duration=5, threshold_f=1.5, max_wait=60):
    """
    Recondition a sensor by running a high-heat cycle and waiting for cooldown.
    Optionally uses another sensor for cooldown comparison.
    """
    heat_sensor(sensor, duration=heat_duration)
    cooldown_sensors(sensor, sensor_ref, threshold_f=threshold_f, max_wait=max_wait)


# from sensor_utils import recondition_sensor
#
# # Example: recondition internal sensor, using external as cooldown reference
# recondition_sensor(internal_sensor, sensor_ref=external_sensor)
#
# # Or just recondition one without a reference
# recondition_sensor(internal_sensor)
