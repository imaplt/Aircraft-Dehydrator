import psutil
import os
import glob

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
            "logs": log_file_sizes(log_dir=log_dir)
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
    """
    Report sizes of output.log, log.csv, and rotated archives (log.csv.1, log.csv.2, …).
    """
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
