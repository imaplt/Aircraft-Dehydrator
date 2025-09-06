import psutil
import os
import glob
from config_manager import ConfigManager

configManager = ConfigManager('config.ini')

def get_system_stats(log_dir="."):
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
            "cpu_temp": get_cpu_temp(temps),
            "logs": log_file_summary(log_dir=log_dir),
            "sensors": sensor_summary_stats()
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

def get_file_size(path):
    """Return file size in human-readable format, or 'Not found' if missing."""
    try:
        size = os.path.getsize(path)
        # Convert to KB/MB dynamically
        for unit in ['B','KB','MB','GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
    except FileNotFoundError:
        return "Not found"

def log_file_sizes(log_dir=".", log_base="log.csv"):
    # Report sizes of output.log, log.csv, and rotated archives (log.csv.1, log.csv.2, …).
    results = {}
    # output.log
    results["output.log"] = get_file_size(os.path.join(log_dir, "output.log"))
    # log.csv (main)
    results[log_base] = get_file_size(os.path.join(log_dir, log_base))
    # archives log.csv.N
    archive_pattern = os.path.join(log_dir, f"{log_base}.*")
    archives = sorted(glob.glob(archive_pattern))
    for fname in archives:
        results[os.path.basename(fname)] = get_file_size(fname)

    print(results)
    return results

def log_file_summary(log_dir=".", log_base="log.csv"):
    """
    Return a one-line summary:
    output.log: XX log.csv: XX log archive count: X log archive total size: XXX
    Sizes are auto-scaled (B, KB, MB, GB).
    """
    output_log = os.path.join(log_dir, "output.log")
    csv_log = os.path.join(log_dir, log_base)
    archive_pattern = os.path.join(log_dir, f"{log_base}.*")

    # Get main file sizes (default to 0 if missing)
    output_size = os.path.getsize(output_log) if os.path.exists(output_log) else 0
    csv_size = os.path.getsize(csv_log) if os.path.exists(csv_log) else 0

    # Gather archives
    archives = sorted(glob.glob(archive_pattern))
    archive_count = len(archives)
    archive_total = sum(os.path.getsize(f) for f in archives)

    def fmt(size_bytes):
        """Format size dynamically with 1 decimal place."""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.1f}{unit}"
            size /= 1024
    print(
        f"output.log: {fmt(output_size)} "
        f"{log_base}: {fmt(csv_size)} "
        f"log archive count: {archive_count} "
        f"log archive total size: {fmt(archive_total)}"
    )
    return (
        f"output.log: {fmt(output_size)} "
        f"{log_base}: {fmt(csv_size)} "
        f"log archive count: {archive_count} "
        f"log archive total size: {fmt(archive_total)}"
    )

def sensor_summary_stats():
    """
    Return multi-line summary for internal, external, and fan stats.
    Uses global config variables already loaded.
    """
    # Initialise the logging and pull numbers from the config.
    INTERNAL_HIGH_TEMP = configManager.get_float_config('LOG', 'internal_high_temp')
    INTERNAL_LOW_TEMP = configManager.get_float_config('LOG', 'internal_low_temp')
    INTERNAL_HIGH_HUMIDITY = configManager.get_float_config('LOG', 'internal_high_humidity')
    INTERNAL_LOW_HUMIDITY = configManager.get_float_config('LOG', 'internal_low_humidity')
    EXTERNAL_HIGH_TEMP = configManager.get_float_config('LOG', 'external_high_temp')
    EXTERNAL_LOW_TEMP = configManager.get_float_config('LOG', 'external_low_temp')
    EXTERNAL_HIGH_HUMIDITY = configManager.get_float_config('LOG', 'external_high_humidity')
    EXTERNAL_LOW_HUMIDITY = configManager.get_float_config('LOG', 'external_low_humidity')
    CYCLE_COUNT = configManager.get_int_config('cycle_count')
    FAN_TOTAL_DURATION = configManager.get_duration_config('LOG', 'FAN_TOTAL_DURATION')
    FAN_MAX_RUNTIME = configManager.get_duration_config('LOG', 'FAN_MAX_RUNTIME')
    # Internal environment
    internal_line = (
        f"Internal Temp: {INTERNAL_LOW_TEMP:.1f}–{INTERNAL_HIGH_TEMP:.1f}°F  "
        f"Humidity: {INTERNAL_LOW_HUMIDITY:.1f}–{INTERNAL_HIGH_HUMIDITY:.1f}%"
    )
    print(internal_line)
    # External environment
    external_line = (
        f"External Temp: {EXTERNAL_LOW_TEMP:.1f}–{EXTERNAL_HIGH_TEMP:.1f}°F  "
        f"Humidity: {EXTERNAL_LOW_HUMIDITY:.1f}–{EXTERNAL_HIGH_HUMIDITY:.1f}%"
    )
    print(external_line)
    # Fan stats
    fan_line = (
        f"Fan → Cycles: {CYCLE_COUNT}  "
        f"Total Runtime: {FAN_TOTAL_DURATION}  "
        f"Max Runtime: {FAN_MAX_RUNTIME}"
    )
    print(fan_line)
    return " ".join([internal_line, external_line, fan_line])
    # return "\n".join([internal_line, external_line, fan_line])
