import os
import time
import psutil
import platform
import flask

def performance():
    uptime_seconds = time.time() - psutil.boot_time()
    uptime = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))

    stats = {
        "CPU Usage": f"{psutil.cpu_percent()}%",
        "Memory Usage": f"{psutil.virtual_memory().percent}%",
        "Disk Usage": f"{psutil.disk_usage('/').percent}%",
        "Uptime": uptime,
        "Total RAM": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
        "Available RAM": f"{round(psutil.virtual_memory().available / (1024**3), 2)} GB",
        "OS": platform.system(),
        "Hostname": platform.node(),
        "Python Version": platform.python_version(),
    }

    try:
        load_avg = os.getloadavg()
        stats["Load Average"] = ", ".join(map(str, load_avg))
    except Exception:
        stats["Load Average"] = "N/A"

    return flask.render_template('performance.html', stats=stats,global_html=flask.current_app.config.get('global_html'))

def register_performance_routes(app):
    app.add_url_rule('/performance', 'performance', performance)

