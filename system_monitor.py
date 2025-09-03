import psutil
import os
import time

def get_system_stats():
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)  # very short sample
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        temps = psutil.sensors_temperatures()

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": mem.percent,
            "memory_used_mb": mem.used // (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free // (1024 * 1024 * 1024),
            "cpu_temp": get_cpu_temp(temps)
        }
    except Exception as e:
        return {"error": str(e)}

def get_cpu_temp(temps):
    # On Raspberry Pi, "cpu-thermal" or "cpu_thermal" is usually reported
    if "cpu-thermal" in temps:
        return temps["cpu-thermal"][0].current
    elif "cpu_thermal" in temps:
        return temps["cpu_thermal"][0].current
    else:
        # Fallback to Pi-specific file if psutil doesn't return temps
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return int(f.read()) / 1000.0
        except:
            return None
