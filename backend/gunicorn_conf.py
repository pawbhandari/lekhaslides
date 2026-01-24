import multiprocessing
import os

# WORKAROUND: macOS Gunicorn Fork Safety Crash
# Must be set before any other imports/processing
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

# Worker Options
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 4  # Explicitly set to 4 to match our ThreadPoolExecutor logic
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120  # 2 minutes for long slide generations
keepalive = 5

# Binding
bind = "0.0.0.0:8000"

# Logging
loglevel = "info"
accesslog = "-"  # Stdout
errorlog = "-"   # Stderr

# Process Naming
proc_name = "lekhaslides-backend"
