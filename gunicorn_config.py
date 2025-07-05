#!/usr/bin/env python3
"""
Gunicorn configuration for Impetus production deployment
"""

import multiprocessing
import os

# Server socket
bind = f"{os.environ.get('SERVER_HOST', '0.0.0.0')}:{os.environ.get('SERVER_PORT', '8080')}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = os.environ.get('ACCESS_LOG', '-')
errorlog = os.environ.get('ERROR_LOG', '-')
loglevel = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'impetus-llm-server'

# Server mechanics
daemon = False
pidfile = '/tmp/impetus-gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL/TLS
keyfile = os.environ.get('SSL_KEY_PATH')
certfile = os.environ.get('SSL_CERT_PATH')

# Server hooks
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def on_starting(server):
    server.log.info("Starting Impetus LLM Server")

def on_reload(server):
    server.log.info("Reloading Impetus LLM Server")

# Environment-specific settings
if os.environ.get('FLASK_ENV') == 'development':
    reload = True
    reload_extra_files = ['gerdsen_ai_server/src/**/*.py']
else:
    reload = False

# Thread options (if using threaded workers)
threads = 1

# Request handling
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190