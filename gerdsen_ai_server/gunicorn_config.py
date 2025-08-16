"""
Gunicorn configuration for Impetus LLM Server
Optimized for Apple Silicon hardware
"""

import multiprocessing
import os
from pathlib import Path

# Server socket - secure local-only binding by default
bind = f"{os.getenv('IMPETUS_HOST', '127.0.0.1')}:{os.getenv('IMPETUS_PORT', '8080')}"
backlog = 2048

# Worker processes
# For Apple Silicon, we use fewer workers due to unified memory architecture
# and the fact that ML models are memory-intensive
workers = min(multiprocessing.cpu_count() // 2, 4)  # Max 4 workers
worker_class = 'eventlet'  # Required for Flask-SocketIO
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 300  # 5 minutes for long-running inference requests
graceful_timeout = 120
keepalive = 5

# Process naming
proc_name = 'impetus-llm-server'

# Server mechanics
daemon = False
pidfile = '/tmp/impetus-llm-server.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
errorlog = '-'  # Log to stderr
loglevel = os.getenv('IMPETUS_LOG_LEVEL', 'info').lower()
accesslog = '-' if os.getenv('IMPETUS_ACCESS_LOG', 'false').lower() == 'true' else None
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process lifecycle
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Impetus LLM Server...")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Worker class: {worker_class}")
    server.log.info(f"Timeout: {timeout}s")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Impetus LLM Server...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Impetus LLM Server is ready. Listening on: {}".format(bind))

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker interrupted: {}".format(worker.pid))

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Forking worker: {}".format(worker))

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned: {}".format(worker.pid))

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forking new master process...")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("Shutting down Impetus LLM Server...")

# StatsD integration (optional)
statsd_host = os.getenv('STATSD_HOST', None)
if statsd_host:
    statsd_prefix = 'impetus.llm.server'

# Environment
raw_env = []
for key, value in os.environ.items():
    if key.startswith('IMPETUS_'):
        raw_env.append(f"{key}={value}")

# SSL/TLS (optional)
keyfile = os.getenv('IMPETUS_SSL_KEY', None)
certfile = os.getenv('IMPETUS_SSL_CERT', None)

# Thread options
threads = 1  # Single thread per worker for ML workloads

# Request handling
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server optimization for Apple Silicon
# Disable sendfile to prevent issues with unified memory
sendfile = False

# Preload app for better memory efficiency with ML models
preload_app = True

# Worker memory monitoring (restart workers if they consume too much memory)
# This is important for ML workloads that can have memory leaks
max_worker_memory_mb = int(os.getenv('IMPETUS_MAX_WORKER_MEMORY_MB', '4096'))

def post_worker_init(worker):
    """Monitor worker memory usage."""
    import psutil
    import threading
    import time
    
    def check_memory():
        while True:
            try:
                process = psutil.Process(os.getpid())
                mem_mb = process.memory_info().rss / 1024 / 1024
                if mem_mb > max_worker_memory_mb:
                    worker.log.warning(f"Worker {worker.pid} memory usage ({mem_mb:.1f}MB) exceeds limit ({max_worker_memory_mb}MB)")
                    os.kill(os.getpid(), signal.SIGTERM)
                    break
            except:
                break
            time.sleep(30)  # Check every 30 seconds
    
    # Start memory monitoring thread
    monitor_thread = threading.Thread(target=check_memory, daemon=True)
    monitor_thread.start()

# Import signal for memory monitoring
import signal